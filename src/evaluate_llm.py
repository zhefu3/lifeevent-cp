"""v1 evaluation: conformal over LLM scores + TF-IDF vs LLM comparison table.

Reuses the exact same conformal and metric code paths as the TF-IDF baseline; the only
difference is where candidate_scores come from. q_hats are fitted on the LLM's OWN
calibration scores (each score source needs its own calibration — thresholds are not
transferable between models).
"""

from __future__ import annotations

import csv
import json
from typing import Any

from .conformal import attach_sets, calibration_scores, fit_all_qhats
from .evaluate import evaluate, write_example_cases
from .utils import PROJECT_ROOT, load_config, read_jsonl, setup_logging, write_json, write_jsonl

LOG = setup_logging()


def main() -> None:
    config = load_config()
    outdir = PROJECT_ROOT / "outputs" / "llm"
    preds = list(read_jsonl(outdir / "predictions_llm.jsonl"))
    cal = [p for p in preds if p["split"] == "calibration"]
    test = [p for p in preds if p["split"] == "test"]
    n_fail = sum(1 for p in preds if not p.get("parse_ok", True))

    q_hats = fit_all_qhats(calibration_scores(cal), [float(a) for a in config["alphas"]])
    write_json(outdir / "qhats_llm.json", {"n_calibration": len(cal), "q_hats": q_hats,
                                           "n_parse_fail_total": n_fail})
    test_with_sets = attach_sets(test, q_hats)
    write_jsonl(outdir / "predictions_llm.jsonl", [p for p in preds if p["split"] == "calibration"] + test_with_sets)

    test_qs = [q for q in read_jsonl(PROJECT_ROOT / "data" / "splits" / "test.jsonl")]
    summary = evaluate(test_qs, test_with_sets, outdir)
    write_example_cases(test_qs, test_with_sets, outdir)

    # Side-by-side comparison against the TF-IDF baseline (canonical outputs/).
    def _overall(path):
        return {r["coverage_target"]: r for r in csv.DictReader(open(path)) if r["group"] == "overall"}
    tf = _overall(PROJECT_ROOT / "outputs" / "coverage_table.csv")
    llm = _overall(outdir / "coverage_table.csv")
    tf_manifest = json.loads((PROJECT_ROOT / "outputs" / "run_manifest_full.json").read_text())
    lines = ["# TF-IDF vs LLM（同一 500 题、同一 conformal 骨架）", "",
             f"- TF-IDF 点准确率 {tf_manifest['summary']['point_accuracy']}, LLM 点准确率 {summary['point_accuracy']}"
             f"（LLM 解析失败回退均匀分布共 {n_fail} 题，已计入）", "",
             "| 目标覆盖 | TF-IDF 实测 | LLM 实测 | TF-IDF 平均集合 | LLM 平均集合 | TF-IDF 全集率 | LLM 全集率 |",
             "|---|---|---|---|---|---|---|"]
    for cov in sorted(tf):
        lines.append(f"| {cov} | {tf[cov]['empirical_coverage']} | {llm[cov]['empirical_coverage']} | "
                     f"{tf[cov]['avg_set_size']} | {llm[cov]['avg_set_size']} | "
                     f"{tf[cov]['full_set_rate']} | {llm[cov]['full_set_rate']} |")
    (outdir / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    LOG.info("LLM eval done: acc=%s, comparison -> %s", summary["point_accuracy"], outdir / "comparison.md")


if __name__ == "__main__":
    main()
