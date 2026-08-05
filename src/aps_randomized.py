"""Randomized APS + calibration-set-size study — zero new model calls.

1. Randomized APS (Romano et al. 2020 style): calibration score subtracts a uniform
   share u*p(true) of the true candidate's own mass; at prediction time the boundary
   candidate is included only with the matching probability. Removes the systematic
   over-coverage of the conservative variant. Uses the project seed.
2. Calibration-size study: subsample n_cal in {20, 50, 100} from the calibration pool
   (200 resamples each, seeded), fit LAC q_hat, measure test coverage @0.90 — reports
   the spread (5th/95th percentile band) of empirical coverage as a function of n_cal.

Outputs: outputs/aps_randomized.json + appended tables in outputs/conformal_extras.md.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .conformal import calibration_scores, fit_qhat, prediction_set
from .evaluate import wilson_ci
from .utils import PROJECT_ROOT, get_rng, load_config, read_jsonl, setup_logging, write_json

LOG = setup_logging()


def rand_aps_cal_score(scores: dict[str, float], correct: str, u: float) -> float:
    p_true = scores[correct]
    mass_above = sum(p for p in scores.values() if p > p_true)
    ties_geq = sum(p for p in scores.values() if p == p_true)  # includes true (and exact ties)
    return mass_above + ties_geq - u * p_true


def rand_aps_set(scores: dict[str, float], q_hat: float, u: float) -> list[str]:
    """Mirror of the calibration rule: candidate c (prefix mass rho) enters iff
    rho + (1-u)*p_c <= q_hat; first failure stops the scan (rho is monotone)."""
    ranked = sorted(scores, key=lambda c: (-scores[c], c))
    out, cum = [], 0.0
    for c in ranked:
        if cum + (1.0 - u) * scores[c] <= q_hat:
            out.append(c)
            cum += scores[c]
        else:
            break
    return sorted(out)


def run() -> None:
    config = load_config()
    rng = get_rng(config)
    alphas = [float(a) for a in config["alphas"]]
    sources = {"tfidf": list(read_jsonl(PROJECT_ROOT / "outputs" / "predictions.jsonl")),
               "llm": list(read_jsonl(PROJECT_ROOT / "outputs" / "llm" / "predictions_llm.jsonl"))}
    result: dict[str, Any] = {}

    for sname, preds in sources.items():
        cal = [p for p in preds if p["split"] == "calibration"]
        test = [p for p in preds if p["split"] == "test"]
        r: dict[str, Any] = {"randomized_aps": {}, "cal_size_study": {}}

        u_cal = rng.uniform(size=len(cal))
        u_test = rng.uniform(size=len(test))
        cal_scores = np.array([rand_aps_cal_score(p["candidate_scores"], p["correct_candidate_id"], u)
                               for p, u in zip(cal, u_cal)])
        for a in alphas:
            cov_key = f"{1 - a:.2f}"
            q = fit_qhat(np.clip(cal_scores, 0, None), a)
            sets = [rand_aps_set(p["candidate_scores"], q, u) for p, u in zip(test, u_test)]
            covered = sum(p["correct_candidate_id"] in s for p, s in zip(test, sets))
            lo, hi = wilson_ci(covered, len(test))
            r["randomized_aps"][cov_key] = {
                "q_hat": round(float(q), 4), "coverage": round(covered / len(test), 4),
                "wilson": [round(lo, 4), round(hi, 4)],
                "avg_size": round(sum(len(s) for s in sets) / len(test), 2),
                "empty_rate": round(sum(1 for s in sets if not s) / len(test), 3)}

        lac_scores = calibration_scores(cal)
        for n_cal in (20, 50, 100):
            covs = []
            for _ in range(200):
                idx = rng.choice(len(lac_scores), size=n_cal, replace=False)
                q = fit_qhat(lac_scores[idx], 0.10)
                covered = sum(p["correct_candidate_id"] in prediction_set(p["candidate_scores"], q)
                              for p in test)
                covs.append(covered / len(test))
            covs = np.array(covs)
            r["cal_size_study"][str(n_cal)] = {
                "mean_cov@0.90": round(float(covs.mean()), 4),
                "p5": round(float(np.percentile(covs, 5)), 3),
                "p95": round(float(np.percentile(covs, 95)), 3)}
        result[sname] = r

    write_json(PROJECT_ROOT / "outputs" / "aps_randomized.json", result)
    lines = ["", "## 随机化 APS（同 seed，对照上表非随机版）", ""]
    for sname, r in result.items():
        lines.append(f"**{sname}**：" + "；".join(
            f"@{cov} 覆盖 {v['coverage']:.2f} [{v['wilson'][0]:.2f},{v['wilson'][1]:.2f}] 平均集合 {v['avg_size']}"
            for cov, v in sorted(r["randomized_aps"].items())))
    lines += ["", "## 校准集大小研究（LAC @0.90，各 200 次重抽，test 覆盖的 5%–95% 分位带）", ""]
    for sname, r in result.items():
        lines.append(f"**{sname}**：" + "；".join(
            f"n_cal={n} 均值 {v['mean_cov@0.90']:.3f} 带 [{v['p5']:.2f}, {v['p95']:.2f}]"
            for n, v in sorted(r["cal_size_study"].items(), key=lambda kv: int(kv[0]))))
    with open(PROJECT_ROOT / "outputs" / "conformal_extras.md", "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    LOG.info("randomized APS + cal-size study appended to conformal_extras.md")


if __name__ == "__main__":
    run()
