"""Practices adopted from the similar-projects survey (2026-08-04) — zero new model
calls. Sources are cited per block; see 02-调研报告 for the adoption matrix.

1. Frequency-prior baseline (EdgeBank, Poursafaei et al. NeurIPS 2022): how much
   accuracy the dataset prior gives away for free — third reference column.
2. Conformal p-values + KS uniformity test (crepes): under exchangeability the true
   label's smoothed p-value must be U(0,1); plus a two-sample KS between probe-identified
   and unidentified questions (contamination vs conformal validity).
3. Brier score (alongside ECE; Tian et al. EMNLP 2023 calibration practice).
4. PRR selective-prediction metric (LM-Polygraph): rejection curve by uncertainty.
5. Answer-letter chi-square audit (PriDe, ICLR 2024: MCQ selection bias).
6. Alpha sweep 0.02..0.96 (MAPIE tutorial convention) -> outputs/alpha_sweep.csv.
7. Coverage distribution over R=100 person-level cal/test resplits vs the analytic
   Beta(n+1-l, l) band (Angelopoulos & Bates tutorial protocol).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import numpy as np
from scipy import stats

from .conformal import calibration_scores, fit_all_qhats, fit_qhat, prediction_set
from .utils import PROJECT_ROOT, get_rng, load_config, read_json, read_jsonl, setup_logging, write_json

LOG = setup_logging()


def _person(qid: str) -> str:
    return qid.split("_")[0]


def _cov_size(preds: list[dict[str, Any]], q: float) -> tuple[float, float]:
    sets = [prediction_set(p["candidate_scores"], q) for p in preds]
    cov = sum(p["correct_candidate_id"] in s for p, s in zip(preds, sets)) / len(preds)
    return cov, sum(len(s) for s in sets) / len(preds)


def frequency_baseline(questions: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    train_counts: Counter = Counter()
    for q in questions:
        if q["split"] == "train":
            correct = next(c for c in q["candidates"] if c["candidate_id"] == q["correct_candidate_id"])
            train_counts[correct["target_id"]] += 1
    # also count all train-person events? deliberately only correct answers of train
    # questions: the "answer prior" a frequency cheater could learn from the benchmark.
    preds = []
    for q in questions:
        if q["split"] == "train":
            continue
        raw = {c["candidate_id"]: train_counts[c["target_id"]] + 1.0 for c in q["candidates"]}
        total = sum(raw.values())
        scores = {k: v / total for k, v in raw.items()}
        point = max(scores, key=lambda c: (scores[c], c))
        preds.append({"question_id": q["question_id"], "split": q["split"],
                      "candidate_scores": scores, "point_prediction": point,
                      "correct_candidate_id": q["correct_candidate_id"]})
    cal = [p for p in preds if p["split"] == "calibration"]
    test = [p for p in preds if p["split"] == "test"]
    q_hats = fit_all_qhats(calibration_scores(cal), [float(a) for a in config["alphas"]])
    out = {"accuracy": round(sum(p["point_prediction"] == p["correct_candidate_id"] for p in test) / len(test), 4)}
    for cov, qh in sorted(q_hats.items()):
        c, s = _cov_size(test, qh)
        out[cov] = {"coverage": round(c, 4), "avg_size": round(s, 2)}
    return out


def smoothed_pvalue(score: float, cal_scores: np.ndarray, u: float) -> float:
    n_greater = int(np.sum(cal_scores > score))
    n_equal = int(np.sum(cal_scores == score))
    return (n_greater + u * (n_equal + 1)) / (len(cal_scores) + 1)


def pvalue_block(preds: list[dict[str, Any]], probe_rows: dict[str, bool] | None,
                 rng: np.random.Generator) -> dict[str, Any]:
    cal = [p for p in preds if p["split"] == "calibration"]
    test = [p for p in preds if p["split"] == "test"]
    cal_s = calibration_scores(cal)
    pvals, ident, unident = [], [], []
    for p in test:
        s = 1.0 - p["candidate_scores"][p["correct_candidate_id"]]
        pv = smoothed_pvalue(s, cal_s, float(rng.uniform()))
        pvals.append(pv)
        if probe_rows is not None and p["question_id"] in probe_rows:
            (ident if probe_rows[p["question_id"]] else unident).append(pv)
    ks = stats.kstest(pvals, "uniform")
    out = {"ks_uniform_stat": round(float(ks.statistic), 4), "ks_uniform_pvalue": round(float(ks.pvalue), 4)}
    if ident and unident:
        ks2 = stats.ks_2samp(ident, unident)
        out["probe_ks2_stat"] = round(float(ks2.statistic), 4)
        out["probe_ks2_pvalue"] = round(float(ks2.pvalue), 4)
        out["n_identified"], out["n_unidentified"] = len(ident), len(unident)
    return out


def brier(preds: list[dict[str, Any]]) -> float:
    total = 0.0
    test = [p for p in preds if p["split"] == "test"]
    for p in test:
        for cid, pr in p["candidate_scores"].items():
            y = 1.0 if cid == p["correct_candidate_id"] else 0.0
            total += (pr - y) ** 2
    return round(total / len(test), 4)


def prr(preds: list[dict[str, Any]]) -> dict[str, Any]:
    """Prediction Rejection Ratio: how much better than random the uncertainty
    ordering is at rejecting errors (1 = oracle, 0 = random)."""
    test = [p for p in preds if p["split"] == "test"]
    correct = np.array([p["point_prediction"] == p["correct_candidate_id"] for p in test], float)
    unc = np.array([1.0 - max(p["candidate_scores"].values()) for p in test])

    def _area(order: np.ndarray) -> float:
        acc_curve = [correct[order[:k]].mean() for k in range(1, len(order) + 1)]
        return float(np.mean(acc_curve))

    by_conf = _area(np.argsort(unc, kind="stable"))
    oracle = _area(np.argsort(-correct, kind="stable"))
    random_area = float(correct.mean())
    denom = oracle - random_area
    out = {"prr": round((by_conf - random_area) / denom, 4) if denom > 0 else None,
           "acc_keep50": round(float(correct[np.argsort(unc, kind="stable")[: len(test) // 2]].mean()), 4)}
    return out


def letter_chi2(preds: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(p["point_prediction"] for p in preds)
    obs = [counts.get(c, 0) for c in "ABCDEF"]
    chi = stats.chisquare(obs)
    return {"counts": dict(zip("ABCDEF", obs)), "chi2": round(float(chi.statistic), 3),
            "pvalue": round(float(chi.pvalue), 4)}


def alpha_sweep(preds: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    cal = [p for p in preds if p["split"] == "calibration"]
    test = [p for p in preds if p["split"] == "test"]
    cal_s = calibration_scores(cal)
    rows = []
    for alpha in np.arange(0.02, 0.98, 0.02):
        qh = fit_qhat(cal_s, float(alpha))
        c, s = _cov_size(test, qh)
        rows.append({"source": name, "alpha": round(float(alpha), 2), "target": round(1 - float(alpha), 2),
                     "coverage": round(c, 4), "avg_size": round(s, 2)})
    return rows


def coverage_distribution(preds: list[dict[str, Any]], rng: np.random.Generator,
                          alphas: list[float], r_splits: int = 100) -> dict[str, Any]:
    pool = [p for p in preds if p["split"] in ("calibration", "test")]
    persons = sorted({_person(p["question_id"]) for p in pool})
    out: dict[str, Any] = {}
    covs_by_alpha: dict[float, list[float]] = {a: [] for a in alphas}
    n_cal_used = []
    for _ in range(r_splits):
        order = rng.permutation(len(persons))
        half = set(persons[i] for i in order[: len(persons) // 2])
        cal = [p for p in pool if _person(p["question_id"]) in half]
        test = [p for p in pool if _person(p["question_id"]) not in half]
        cal_s = calibration_scores(cal)
        n_cal_used.append(len(cal))
        for a in alphas:
            qh = fit_qhat(cal_s, a)
            c, _ = _cov_size(test, qh)
            covs_by_alpha[a].append(c)
    for a in alphas:
        arr = np.array(covs_by_alpha[a])
        n = int(np.median(n_cal_used))
        l = int(np.floor((n + 1) * a))
        beta_lo, beta_hi = (stats.beta.ppf([0.05, 0.95], n + 1 - l, l) if l > 0 else (1.0, 1.0))
        out[f"{1 - a:.2f}"] = {"empirical_mean": round(float(arr.mean()), 4),
                               "empirical_p5_p95": [round(float(np.percentile(arr, 5)), 3),
                                                    round(float(np.percentile(arr, 95)), 3)],
                               "beta_p5_p95": [round(float(beta_lo), 3), round(float(beta_hi), 3)],
                               "n_cal_median": n}
    return out


def run() -> None:
    config = load_config()
    rng = get_rng(config)
    alphas = [float(a) for a in config["alphas"]]
    questions = read_json(PROJECT_ROOT / "data" / "processed" / "life_event_questions.json")
    sources = {"tfidf": list(read_jsonl(PROJECT_ROOT / "outputs" / "predictions.jsonl")),
               "llm": list(read_jsonl(PROJECT_ROOT / "outputs" / "llm" / "predictions_llm.jsonl"))}
    probe_path = PROJECT_ROOT / "outputs" / "llm" / "contamination_probe.json"
    probe = ({r["question_id"]: r["hit"] for r in read_json(probe_path)["rows"]}
             if probe_path.exists() else None)

    result: dict[str, Any] = {"frequency_baseline": frequency_baseline(questions, config)}
    sweep_rows: list[dict[str, Any]] = []
    for name, preds in sources.items():
        result[name] = {
            "pvalues": pvalue_block(preds, probe if name == "llm" else None, rng),
            "brier_test": brier(preds),
            "prr": prr(preds),
            "letter_chi2": letter_chi2(preds),
            "coverage_distribution_R100": coverage_distribution(preds, rng, alphas),
        }
        sweep_rows.extend(alpha_sweep(preds, name))

    write_json(PROJECT_ROOT / "outputs" / "survey_adoptions.json", result)
    import csv as _csv
    with open(PROJECT_ROOT / "outputs" / "alpha_sweep.csv", "w", newline="", encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(sweep_rows[0].keys()))
        w.writeheader()
        w.writerows(sweep_rows)

    fb = result["frequency_baseline"]
    lines = ["# 调研采纳指标（零新调用）", "",
             f"## 频率先验基线（EdgeBank 式第三参照）",
             f"- 准确率 {fb['accuracy']}（对照 TF-IDF 0.14 / LLM 0.68 / 随机 0.167）；" +
             "；".join(f"@{c} 覆盖 {v['coverage']} 集合 {v['avg_size']}" for c, v in fb.items() if c != "accuracy"), ""]
    for name in sources:
        r = result[name]
        lines += [f"## {name}",
                  f"- conformal p-value KS 均匀性：stat={r['pvalues']['ks_uniform_stat']} p={r['pvalues']['ks_uniform_pvalue']}"
                  + (f"；认出/未认出两样本 KS p={r['pvalues'].get('probe_ks2_pvalue')}" if "probe_ks2_pvalue" in r["pvalues"] else ""),
                  f"- Brier {r['brier_test']}；PRR {r['prr']['prr']}（按不确定度保留前 50% 时准确率 {r['prr']['acc_keep50']}）",
                  f"- 选项字母卡方：{r['letter_chi2']['counts']} chi2={r['letter_chi2']['chi2']} p={r['letter_chi2']['pvalue']}",
                  "- R=100 按人重划分覆盖分布 vs Beta 理论带：" +
                  "；".join(f"@{c} 实测均值 {v['empirical_mean']} 带 {v['empirical_p5_p95']} 理论 {v['beta_p5_p95']}"
                            for c, v in sorted(r["coverage_distribution_R100"].items())), ""]
    (PROJECT_ROOT / "outputs" / "survey_adoptions.md").write_text("\n".join(lines), encoding="utf-8")
    LOG.info("survey adoptions -> outputs/survey_adoptions.md")


if __name__ == "__main__":
    run()
