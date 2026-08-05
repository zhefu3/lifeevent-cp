"""Method extensions over existing scores — zero new model calls.

1. APS (Adaptive Prediction Sets, non-randomized/conservative variant): calibration
   score = cumulative probability mass down to and including the true candidate
   (candidates sorted by descending probability). Sets take candidates until the
   cumulative mass reaches q_hat — never empty by construction.
2. Mondrian / class-conditional LAC: one threshold per hidden_event_type, calibrated
   on that type's calibration questions only. The textbook remedy for the group
   coverage disparities exposed by the v3 shift experiment — at the price of tiny
   per-group calibration sets (finite-sample quantile snaps to max -> full sets).
3. ECE (10 bins, max-probability binning) for both score sources.

Outputs: outputs/conformal_extras.{json,md}.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from .conformal import calibration_scores, fit_all_qhats, fit_qhat, prediction_set
from .evaluate import wilson_ci
from .utils import PROJECT_ROOT, load_config, read_json, read_jsonl, setup_logging, write_json

LOG = setup_logging()


def aps_score(scores: dict[str, float], correct: str) -> float:
    """Cumulative mass of candidates with prob >= p(correct), including correct."""
    p_true = scores[correct]
    return sum(p for p in scores.values() if p >= p_true)


def aps_set(scores: dict[str, float], q_hat: float) -> list[str]:
    ranked = sorted(scores, key=lambda c: (-scores[c], c))
    out, cum = [], 0.0
    for c in ranked:
        out.append(c)
        cum += scores[c]
        if cum >= q_hat:
            break
    return sorted(out)


def _coverage_sizes(test: list[dict[str, Any]], sets: list[list[str]]) -> tuple[float, float, tuple[float, float]]:
    covered = sum(p["correct_candidate_id"] in s for p, s in zip(test, sets))
    lo, hi = wilson_ci(covered, len(test))
    return covered / len(test), sum(len(s) for s in sets) / len(test), (lo, hi)


def run() -> None:
    config = load_config()
    alphas = [float(a) for a in config["alphas"]]
    meta = {q["question_id"]: q for q in read_json(PROJECT_ROOT / "data" / "processed" / "life_event_questions.json")}
    sources = {"tfidf": list(read_jsonl(PROJECT_ROOT / "outputs" / "predictions.jsonl")),
               "llm": list(read_jsonl(PROJECT_ROOT / "outputs" / "llm" / "predictions_llm.jsonl"))}
    result: dict[str, Any] = {}

    for sname, preds in sources.items():
        cal = [p for p in preds if p["split"] == "calibration"]
        test = [p for p in preds if p["split"] == "test"]
        r: dict[str, Any] = {}

        # --- APS ---
        aps_cal = np.array([aps_score(p["candidate_scores"], p["correct_candidate_id"]) for p in cal])
        aps_block: dict[str, Any] = {}
        for a in alphas:
            cov_key = f"{1 - a:.2f}"
            q = fit_qhat(aps_cal, a)
            sets = [aps_set(p["candidate_scores"], q) for p in test]
            c, s, ci = _coverage_sizes(test, sets)
            aps_block[cov_key] = {"q_hat": round(q, 4), "coverage": round(c, 4),
                                  "wilson": [round(ci[0], 4), round(ci[1], 4)], "avg_size": round(s, 2)}
        r["aps"] = aps_block

        # --- Mondrian LAC by hidden_event_type ---
        by_type_cal: dict[str, list] = defaultdict(list)
        for p in cal:
            by_type_cal[meta[p["question_id"]]["hidden_event_type"]].append(p)
        mond: dict[str, Any] = {"per_type_qhat": {}, "levels": {}}
        for a in alphas:
            cov_key = f"{1 - a:.2f}"
            qs = {t: fit_qhat(calibration_scores(rows), a) for t, rows in sorted(by_type_cal.items())}
            mond["per_type_qhat"][cov_key] = {t: round(v, 4) for t, v in qs.items()}
            per_type: dict[str, Any] = {}
            all_sets, all_test = [], []
            for p in test:
                t = meta[p["question_id"]]["hidden_event_type"]
                s = prediction_set(p["candidate_scores"], qs[t])
                all_sets.append(s)
                all_test.append(p)
                per_type.setdefault(t, {"n": 0, "covered": 0, "size": 0})
                per_type[t]["n"] += 1
                per_type[t]["covered"] += p["correct_candidate_id"] in s
                per_type[t]["size"] += len(s)
            c, s_, ci = _coverage_sizes(all_test, all_sets)
            mond["levels"][cov_key] = {
                "overall": {"coverage": round(c, 4), "wilson": [round(ci[0], 4), round(ci[1], 4)],
                            "avg_size": round(s_, 2)},
                "per_type": {t: {"n": v["n"], "coverage": round(v["covered"] / v["n"], 3),
                                 "avg_size": round(v["size"] / v["n"], 2)} for t, v in sorted(per_type.items())},
                "cal_n_per_type": {t: len(rows) for t, rows in sorted(by_type_cal.items())}}
        r["mondrian"] = mond

        # --- ECE (10 bins on max prob, test) ---
        p_max = np.array([max(p["candidate_scores"].values()) for p in test])
        correct = np.array([p["point_prediction"] == p["correct_candidate_id"] for p in test], dtype=float)
        bins = np.linspace(0, 1, 11)
        ece, bin_rows = 0.0, []
        for i in range(10):
            mask = (p_max >= bins[i]) & (p_max < bins[i + 1] if i < 9 else p_max <= bins[i + 1])
            if mask.sum() == 0:
                continue
            conf, acc = float(p_max[mask].mean()), float(correct[mask].mean())
            ece += (mask.sum() / len(test)) * abs(conf - acc)
            bin_rows.append({"bin": f"[{bins[i]:.1f},{bins[i+1]:.1f})", "n": int(mask.sum()),
                             "conf": round(conf, 3), "acc": round(acc, 3)})
        r["ece"] = {"ece": round(float(ece), 4), "bins": bin_rows}
        result[sname] = r

    write_json(PROJECT_ROOT / "outputs" / "conformal_extras.json", result)

    lines = ["# 方法扩展：APS 与 Mondrian（类型条件校准）与 ECE — 零新调用", ""]
    for sname, r in result.items():
        lines.append(f"## {sname}")
        lines.append("| 档 | LAC 覆盖/平均集合（参照） | APS 覆盖/平均集合 | Mondrian 覆盖/平均集合 |")
        lines.append("|---|---|---|---|")
        ref = {"tfidf": {"0.80": (0.83, 4.42), "0.90": (0.91, 4.86), "0.95": (0.97, 5.53)},
               "llm": {"0.80": (0.78, 1.45), "0.90": (0.93, 2.35), "0.95": (0.97, 3.67)}}[sname]
        for cov in ("0.80", "0.90", "0.95"):
            a, m = r["aps"][cov], r["mondrian"]["levels"][cov]["overall"]
            lines.append(f"| {cov} | {ref[cov][0]:.2f} / {ref[cov][1]:.2f} | "
                         f"{a['coverage']:.2f} / {a['avg_size']:.2f} | {m['coverage']:.2f} / {m['avg_size']:.2f} |")
        pt = r["mondrian"]["levels"]["0.90"]["per_type"]
        lines.append("")
        lines.append("Mondrian @0.90 分类型：" + "；".join(
            f"{t} 覆盖 {v['coverage']} 集合 {v['avg_size']}（test n={v['n']}，cal n={r['mondrian']['levels']['0.90']['cal_n_per_type'][t]}）"
            for t, v in pt.items()))
        lines.append(f"\nECE（10 桶，max-prob）：{r['ece']['ece']}")
        lines.append("")
    (PROJECT_ROOT / "outputs" / "conformal_extras.md").write_text("\n".join(lines), encoding="utf-8")
    LOG.info("extras -> outputs/conformal_extras.md")


if __name__ == "__main__":
    run()
