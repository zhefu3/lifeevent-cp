"""v2: self-reflection pass — the same LLM critiques its own first-pass distribution
and re-scores. Research question (spec v2): does reflection make it BETTER, or merely
MORE CONFIDENT?

Same armour as v1 (membership CLI, cache, timeout/retry/skip, uniform fallback counted).
First-pass distributions come from outputs/llm/predictions_llm.jsonl; reflection output
goes to outputs/llm/predictions_reflect.jsonl. --eval compares pass 1 vs pass 2 and fits
reflection's OWN conformal thresholds on its OWN calibration scores.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np

from .conformal import attach_sets, calibration_scores, fit_all_qhats
from .llm_baseline import LETTERS, _extract_json, call_claude, render_score_prompt
from .utils import PROJECT_ROOT, load_config, read_jsonl, setup_logging, sha1_of, write_json, write_jsonl

LOG = setup_logging()

REFLECT_SUFFIX = """

Your previous answer for this question was: {prev}

Re-examine it critically before answering again:
1. Does the timeline ordering (education -> positions -> awards, era consistency) rule any candidate in or out?
2. Are you favouring a candidate because it merely LOOKS familiar rather than fitting THIS timeline and year?
3. Is your confidence justified, or should the distribution be flatter (or sharper)?

After this self-check, output your final answer: ONLY a JSON object with probabilities for A-F summing to 1."""


def reflect_question(question: dict[str, Any], prev_scores: dict[str, float],
                     model: str, timeout_s: int) -> dict[str, Any]:
    prev = json.dumps({k: round(v, 3) for k, v in sorted(prev_scores.items())})
    prompt = render_score_prompt(question) + REFLECT_SUFFIX.format(prev=prev)
    raw = call_claude(prompt, model, timeout_s, "reflect", f"{question['question_id']}_{sha1_of(prompt)[:12]}")
    scores, ok = None, False
    if raw is not None:
        obj = _extract_json(raw)
        if obj:
            try:
                vals = {c: max(float(obj.get(c, 0.0)), 0.0) for c in LETTERS}
                total = sum(vals.values())
                if total > 0:
                    scores = {c: v / total for c, v in vals.items()}
                    ok = True
            except (TypeError, ValueError):
                pass
    if scores is None:
        scores = dict(prev_scores)  # reflection failed -> keep first-pass answer
    point = max(scores, key=lambda c: (scores[c], c))
    return {"question_id": question["question_id"], "split": question["split"],
            "candidate_scores": scores, "point_prediction": point,
            "correct_candidate_id": question["correct_candidate_id"], "parse_ok": ok}


def run_reflection(model: str, timeout_s: int, workers: int) -> None:
    outdir = PROJECT_ROOT / "outputs" / "llm"
    first = {p["question_id"]: p for p in read_jsonl(outdir / "predictions_llm.jsonl")}
    questions = []
    for split in ("calibration", "test"):
        questions.extend(read_jsonl(PROJECT_ROOT / "data" / "splits" / f"{split}.jsonl"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        preds = list(ex.map(lambda q: reflect_question(
            q, first[q["question_id"]]["candidate_scores"], model, timeout_s), questions))
    n_fail = sum(1 for p in preds if not p["parse_ok"])
    write_jsonl(outdir / "predictions_reflect.jsonl", preds)
    LOG.info("reflection scored %d questions (%d failures kept first-pass answer)", len(preds), n_fail)


def evaluate_reflection() -> None:
    config = load_config()
    outdir = PROJECT_ROOT / "outputs" / "llm"
    first = list(read_jsonl(outdir / "predictions_llm.jsonl"))
    second = list(read_jsonl(outdir / "predictions_reflect.jsonl"))

    def _stats(preds: list[dict[str, Any]]) -> dict[str, Any]:
        test = [p for p in preds if p["split"] == "test"]
        cal = [p for p in preds if p["split"] == "calibration"]
        q_hats = fit_all_qhats(calibration_scores(cal), [float(a) for a in config["alphas"]])
        test = attach_sets(test, q_hats)
        n = len(test)
        out = {"accuracy": sum(p["point_prediction"] == p["correct_candidate_id"] for p in test) / n,
               "mean_p_max": float(np.mean([max(p["candidate_scores"].values()) for p in test])),
               "mean_p_correct": float(np.mean([p["candidate_scores"][p["correct_candidate_id"]] for p in test])),
               "q_hats": q_hats}
        for cov in sorted(q_hats):
            sizes = [len(p["conformal_sets"][cov]) for p in test]
            covered = sum(p["correct_candidate_id"] in p["conformal_sets"][cov] for p in test)
            out[f"cov_{cov}"] = covered / n
            out[f"avg_size_{cov}"] = sum(sizes) / n
        return out

    s1, s2 = _stats(first), _stats(second)
    switched = sum(1 for a, b in zip(sorted(first, key=lambda p: p["question_id"]),
                                     sorted(second, key=lambda p: p["question_id"]))
                   if a["point_prediction"] != b["point_prediction"])
    result = {"pass1": s1, "pass2_reflect": s2, "n_switched_answers": switched}
    write_json(outdir / "reflect_comparison.json", result)
    lines = ["# v2 自反思对比（test = 100，同一 LLM、同一题）", "",
             "| 指标 | 第一遍 | 自反思后 |", "|---|---|---|",
             f"| 点准确率 | {s1['accuracy']:.2f} | {s2['accuracy']:.2f} |",
             f"| 平均最大概率（自信度） | {s1['mean_p_max']:.3f} | {s2['mean_p_max']:.3f} |",
             f"| 平均正确项概率 | {s1['mean_p_correct']:.3f} | {s2['mean_p_correct']:.3f} |"]
    for cov in ("0.80", "0.90", "0.95"):
        lines.append(f"| 覆盖@{cov} / 平均集合 | {s1['cov_'+cov]:.2f} / {s1['avg_size_'+cov]:.2f} "
                     f"| {s2['cov_'+cov]:.2f} / {s2['avg_size_'+cov]:.2f} |")
    lines.append(f"\n改判题数（全部 200 题中）：{switched}")
    (outdir / "reflect_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    LOG.info("reflect eval: acc %.2f -> %.2f, p_max %.3f -> %.3f",
             s1["accuracy"], s2["accuracy"], s1["mean_p_max"], s2["mean_p_max"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", action="store_true", help="compare pass1 vs reflection")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    if args.eval:
        evaluate_reflection()
    else:
        run_reflection(args.model, args.timeout, args.workers)


if __name__ == "__main__":
    main()
