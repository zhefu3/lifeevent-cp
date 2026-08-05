"""v3: coverage under distribution shift — zero new model calls.

Split conformal's marginal guarantee assumes calibration and test are exchangeable.
We break that on purpose, reusing existing scores:

- Type shift: calibrate on non-award questions only, evaluate on award-only test
  questions (and the reverse).
- Era shift: calibrate on missing_year >= 1950, evaluate on pre-1950 test (and reverse).

For each scenario and each score source (TF-IDF, LLM) we report empirical coverage with
Wilson CIs against the in-distribution reference. Small subgroup n means this
demonstrates the DIRECTION of failure, not precise magnitudes — stated in the output.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from .conformal import calibration_scores, fit_all_qhats, prediction_set
from .evaluate import wilson_ci
from .utils import PROJECT_ROOT, load_config, read_json, read_jsonl, setup_logging, write_json

LOG = setup_logging()


def _coverage(preds: list[dict[str, Any]], q_hats: dict[str, float]) -> dict[str, Any]:
    out: dict[str, Any] = {"n": len(preds)}
    for cov, q in sorted(q_hats.items()):
        sets = [prediction_set(p["candidate_scores"], q) for p in preds]
        covered = sum(p["correct_candidate_id"] in s for p, s in zip(preds, sets))
        lo, hi = wilson_ci(covered, len(preds))
        out[cov] = {"coverage": round(covered / len(preds), 4), "wilson": [round(lo, 4), round(hi, 4)],
                    "avg_size": round(sum(len(s) for s in sets) / len(preds), 2)}
    return out


def run() -> None:
    config = load_config()
    alphas = [float(a) for a in config["alphas"]]
    meta = {q["question_id"]: q for q in read_json(PROJECT_ROOT / "data" / "processed" / "life_event_questions.json")}

    sources = {
        "tfidf": list(read_jsonl(PROJECT_ROOT / "outputs" / "predictions.jsonl")),
        "llm": list(read_jsonl(PROJECT_ROOT / "outputs" / "llm" / "predictions_llm.jsonl")),
    }

    def is_award(p: dict[str, Any]) -> bool:
        return meta[p["question_id"]]["hidden_event_type"] == "award"

    def is_pre1950(p: dict[str, Any]) -> bool:
        return meta[p["question_id"]]["missing_year"] < 1950

    scenarios: dict[str, tuple[Callable, Callable]] = {
        # (calibration filter, test filter)
        "in_distribution_reference": (lambda p: True, lambda p: True),
        "cal_nonaward_test_award": (lambda p: not is_award(p), is_award),
        "cal_award_test_nonaward": (is_award, lambda p: not is_award(p)),
        "cal_post1950_test_pre1950": (lambda p: not is_pre1950(p), is_pre1950),
        "cal_pre1950_test_post1950": (is_pre1950, lambda p: not is_pre1950(p)),
    }

    result: dict[str, Any] = {"note": "小子组 n 只演示失效方向，不给精确幅度；判读带 Wilson 区间"}
    for sname, preds in sources.items():
        cal_all = [p for p in preds if p["split"] == "calibration"]
        test_all = [p for p in preds if p["split"] == "test"]
        result[sname] = {}
        for scen, (cal_f, test_f) in scenarios.items():
            cal = [p for p in cal_all if cal_f(p)]
            test = [p for p in test_all if test_f(p)]
            if len(cal) < 15 or len(test) < 10:
                result[sname][scen] = {"skipped": f"n_cal={len(cal)} n_test={len(test)} too small"}
                continue
            q_hats = fit_all_qhats(calibration_scores(cal), alphas)
            result[sname][scen] = {"n_cal": len(cal), "q_hats": {k: round(v, 4) for k, v in q_hats.items()},
                                   **_coverage(test, q_hats)}
    write_json(PROJECT_ROOT / "outputs" / "shift_experiment.json", result)

    lines = ["# v3 shift 实验：故意打破 calibration/test 可交换性（复用既有分数，零新调用）", "",
             "标注：覆盖[Wilson区间]/平均集合；小子组只看方向。", ""]
    for sname in sources:
        lines.append(f"## {sname}")
        lines.append("| 场景 | n_cal / n_test | @0.80 | @0.90 | @0.95 |")
        lines.append("|---|---|---|---|---|")
        for scen, r in result[sname].items():
            if "skipped" in r:
                lines.append(f"| {scen} | {r['skipped']} | - | - | - |")
                continue
            cells = []
            for cov in ("0.80", "0.90", "0.95"):
                c = r[cov]
                cells.append(f"{c['coverage']:.2f} [{c['wilson'][0]:.2f},{c['wilson'][1]:.2f}] / {c['avg_size']}")
            lines.append(f"| {scen} | {r['n_cal']} / {r['n']} | " + " | ".join(cells) + " |")
        lines.append("")
    (PROJECT_ROOT / "outputs" / "shift_experiment.md").write_text("\n".join(lines), encoding="utf-8")
    LOG.info("shift experiment -> outputs/shift_experiment.md")


if __name__ == "__main__":
    run()
