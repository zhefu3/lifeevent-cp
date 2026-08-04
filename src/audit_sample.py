"""Quality-audit sampler: draw 50 questions (seeded), pre-fill the deterministic
columns, leave judgment columns for the human/AI reviewer, and dump full question
content alongside for review.

Usage:  .venv/bin/python -m src.audit_sample [--n 50]
Output: data/audit/audit_sample.csv (+ audit_sample_content.json)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .utils import PROJECT_ROOT, get_rng, load_config, read_json, write_json

COLUMNS = ["question_id", "ground_truth_valid", "hidden_event_not_leaked",
           "candidates_unique", "distractors_plausible", "multiple_possible_answers",
           "timeline_coherent", "reviewer_notes"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    args = ap.parse_args()
    config = load_config()
    rng = get_rng(config)
    questions = read_json(PROJECT_ROOT / config["paths"]["processed_dir"] / "life_event_questions.json")
    idx = rng.choice(len(questions), size=min(args.n, len(questions)), replace=False)
    sample = [questions[int(i)] for i in sorted(idx)]

    outdir = PROJECT_ROOT / "data" / "audit"
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "audit_sample.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for q in sample:
            texts = [c["text"] for c in q["candidates"]]
            leaked = any(o["year"] == q["missing_year"] for o in q["observed_events"])
            w.writerow({"question_id": q["question_id"],
                        "ground_truth_valid": "",  # reviewer judgment
                        "hidden_event_not_leaked": "PASS" if not leaked else "FAIL",
                        "candidates_unique": "PASS" if len(set(texts)) == 6 else "FAIL",
                        "distractors_plausible": "", "multiple_possible_answers": "",
                        "timeline_coherent": "", "reviewer_notes": ""})
    write_json(outdir / "audit_sample_content.json", sample)
    print(f"wrote {len(sample)} rows -> {outdir/'audit_sample.csv'}")


if __name__ == "__main__":
    main()
