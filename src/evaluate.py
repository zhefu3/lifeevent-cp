"""Metrics: point/top-2 accuracy, conformal coverage & efficiency, grouped breakdowns.

Empirical coverage is reported with a Wilson 95% confidence interval; with n=100 test
questions the interval is wide by construction — interpretation must use the interval.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .utils import setup_logging

LOG = setup_logging()


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _year_bucket(year: int) -> str:
    if year < 1950:
        return "<1950"
    if year < 1990:
        return "1950-1989"
    if year < 2010:
        return "1990-2009"
    return "2010+"


def _question_meta(questions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    meta = {}
    for q in questions:
        dtypes = {c["candidate_id"]: c["distractor_type"] for c in q["candidates"]}
        meta[q["question_id"]] = {
            "event_type": q["hidden_event_type"],
            "n_context": len(q["observed_events"]),
            "missing_year": q["missing_year"],
            "year_bucket": _year_bucket(q["missing_year"]),
            "has_same_person": "same_person_wrong_time" in dtypes.values(),
            "dtype_of": dtypes,
        }
    return meta


def _coverage_row(rows: list[dict[str, Any]], cov: str, group: str, value: str) -> dict[str, Any]:
    n = len(rows)
    covered = sum(1 for r in rows if r[f"cover_{cov}"])
    sizes = sorted(r[f"size_{cov}"] for r in rows)
    lo, hi = wilson_ci(covered, n)
    med = sizes[n // 2] if n % 2 else (sizes[n // 2 - 1] + sizes[n // 2]) / 2 if n else 0
    return {"coverage_target": cov, "group": group, "value": value, "n": n,
            "empirical_coverage": round(covered / n, 4) if n else None,
            "coverage_gap": round(covered / n - float(cov), 4) if n else None,
            "wilson_lo": round(lo, 4), "wilson_hi": round(hi, 4),
            "avg_set_size": round(sum(sizes) / n, 3) if n else None,
            "median_set_size": med,
            "singleton_rate": round(sum(1 for s in sizes if s == 1) / n, 4) if n else None,
            "empty_set_rate": round(sum(1 for s in sizes if s == 0) / n, 4) if n else None,
            "full_set_rate": round(sum(1 for s in sizes if s == 6) / n, 4) if n else None}


def evaluate(test_questions: list[dict[str, Any]], test_predictions: list[dict[str, Any]],
             outputs_dir: str | Path) -> dict[str, Any]:
    """Compute all metrics on TEST predictions (which already carry conformal_sets);
    write results.csv + coverage_table.csv and return a summary dict."""
    outdir = Path(outputs_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    meta = _question_meta(test_questions)
    covs = sorted(test_predictions[0]["conformal_sets"].keys()) if test_predictions else []

    rows: list[dict[str, Any]] = []
    for p in test_predictions:
        m = meta[p["question_id"]]
        scores = p["candidate_scores"]
        ranked = sorted(scores, key=lambda c: (-scores[c], c))
        correct = p["correct_candidate_id"]
        row: dict[str, Any] = {
            "question_id": p["question_id"], "event_type": m["event_type"],
            "missing_year": m["missing_year"], "year_bucket": m["year_bucket"],
            "n_context": m["n_context"], "has_same_person": m["has_same_person"],
            "correct_candidate_id": correct, "point_prediction": p["point_prediction"],
            "is_correct": p["point_prediction"] == correct,
            "in_top2": correct in ranked[:2],
            "p_correct": round(scores[correct], 4),
            "rank_correct": ranked.index(correct) + 1,
            "chosen_distractor_type": None if p["point_prediction"] == correct
                                      else m["dtype_of"][p["point_prediction"]],
        }
        for cov in covs:
            s = p["conformal_sets"][cov]
            row[f"set_{cov}"] = "|".join(s)
            row[f"size_{cov}"] = len(s)
            row[f"cover_{cov}"] = correct in s
        rows.append(row)

    n = len(rows)
    summary: dict[str, Any] = {
        "n_test": n,
        "point_accuracy": round(sum(r["is_correct"] for r in rows) / n, 4) if n else None,
        "top2_accuracy": round(sum(r["in_top2"] for r in rows) / n, 4) if n else None,
        "error_chosen_distractor_types": dict(Counter(r["chosen_distractor_type"]
                                                      for r in rows if not r["is_correct"])),
    }

    groupings: dict[str, Any] = {"overall": lambda r: "all", "event_type": lambda r: r["event_type"],
                                 "has_same_person": lambda r: str(r["has_same_person"]),
                                 "n_context": lambda r: str(r["n_context"]),
                                 "year_bucket": lambda r: r["year_bucket"]}
    cov_rows: list[dict[str, Any]] = []
    for cov in covs:
        for gname, fn in groupings.items():
            buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for r in rows:
                buckets[fn(r)].append(r)
            for value in sorted(buckets):
                cov_rows.append(_coverage_row(buckets[value], cov, gname, value))
    summary["coverage_overall"] = [r for r in cov_rows if r["group"] == "overall"]

    if rows:
        with open(outdir / "results.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    if cov_rows:
        with open(outdir / "coverage_table.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(cov_rows[0].keys()))
            w.writeheader()
            w.writerows(cov_rows)
    LOG.info("evaluate: %s", {k: summary[k] for k in ("n_test", "point_accuracy", "top2_accuracy")})
    return summary


def write_example_cases(test_questions: list[dict[str, Any]], test_predictions: list[dict[str, Any]],
                        outputs_dir: str | Path, n_each: int = 5) -> None:
    """5 successes + 5 failures with candidate scores and sets (display keeps names)."""
    qmap = {q["question_id"]: q for q in test_questions}
    succ = [p for p in test_predictions if p["point_prediction"] == p["correct_candidate_id"]][:n_each]
    fail = [p for p in test_predictions if p["point_prediction"] != p["correct_candidate_id"]][:n_each]
    lines = ["# Example cases (test split)", ""]
    for title, batch in (("## Successes", succ), ("## Failures", fail)):
        lines.append(title)
        for p in batch:
            q = qmap[p["question_id"]]
            lines += [f"### {p['question_id']} — {q['person_label']}",
                      f"- missing year: {q['missing_year']} (hidden type: {q['hidden_event_type']})",
                      "- context: " + " | ".join(o["text"] for o in q["observed_events"])]
            for c in q["candidates"]:
                mark = "✓" if c["candidate_id"] == q["correct_candidate_id"] else " "
                lines.append(f"  - [{mark}] {c['candidate_id']} ({c['distractor_type']}, "
                             f"p={p['candidate_scores'][c['candidate_id']]:.3f}): {c['text']}")
            lines.append(f"- point: {p['point_prediction']}; sets: " +
                         "; ".join(f"{cov}→{{{','.join(s)}}}" for cov, s in sorted(p["conformal_sets"].items())))
            lines.append("")
    Path(outputs_dir, "example_cases.md").write_text("\n".join(lines), encoding="utf-8")
