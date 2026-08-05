# LifeEvent-CP v0

**Conformal prediction over masked Wikidata life events — a runnable research prototype.**

Task: given a public figure's partial, year-stamped timeline from Wikidata (up to 2
events before and 2 after), one middle event is hidden. The model scores 6 candidate
events, outputs a single best answer, and constructs split conformal prediction sets at
80% / 90% / 95% target coverage.

This is **not** a "life simulator". Ground truth is the held-out Wikidata statement, not
the only event that could have happened in a real life. See *Scientific scope* below.

## Quick start (macOS, Python 3.11+, CPU only)

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# dry run (small year window, ~50 questions) — always do this first
.venv/bin/python -m src.pipeline --profile dry --stage all

# full run (1850–2026, target 500 questions)
.venv/bin/python -m src.pipeline --profile full --stage all

# tests (12 mandated checks; also validate real artifacts once they exist)
.venv/bin/python -m pytest tests/ -q
```

Stages can be run individually: `--stage fetch | normalize | split | questions | train |
conformal | evaluate`. All SPARQL responses are cached under `data/raw/sparql/`; re-runs
never re-hit the endpoint. All randomness flows from `random_seed: 42` in
`configs/config.yaml`.

## Pipeline

1. **fetch** — two-phase Wikidata harvest (adopted fix E-1):
   *Phase 1 (discovery)*: per (property × time-qualifier × year-slice) queries with
   Blazegraph `rangeSafe` date filters; slices split adaptively on row-cap/timeout, so no
   unstable LIMIT/OFFSET pagination. *Phase 2*: complete timed statements (P69, P108,
   P39, P166; P551 supported but disabled) for the densest persons via VALUES batches.
2. **normalize** — cleaning rules → `data/processed/person_events.jsonl`.
3. **split** — person-level 60/20/20 train/calibration/test (persons never cross splits).
4. **questions** — hide one middle single-event year; 6 candidates: 1 correct,
   2 same_type_near_year, 1 label_similar_same_type, 1 same_person_wrong_time
   (fallback: near-year same-type), 1 same_type_random. Questions lacking 5 legal
   negatives are dropped.
5. **train** — TF-IDF (fit on train records ONLY) + logistic regression; per-question
   softmax over the 6 logits; argmax point prediction.
6. **conformal** — split conformal, LAC score `s = 1 - p(correct)`, finite-sample
   quantile `min(1, ceil((n+1)(1-alpha))/n)` with `np.quantile(..., method="higher")`,
   alphas 0.20/0.10/0.05. Empty sets are allowed and reported.
7. **evaluate** — accuracy, coverage (with Wilson 95% CI), set-size stats, grouped
   breakdowns → `outputs/results.csv`, `outputs/coverage_table.csv`,
   `outputs/example_cases.md`.

## Scientific scope (locked)

The claim is strictly: *recovering an artificially held-out Wikidata event statement
from partial Wikidata timelines*. We do NOT claim: life simulation or prediction; that
"90% coverage" means a specific answer is 90% likely correct; per-individual guarantees;
that events absent from Wikidata did not happen; or that IID guarantees transfer under
distribution shift.

## Repository layout

See the spec in the project archive; notebooks (`notebooks/dataset_builder.ipynb`,
`notebooks/baseline_conformal.ipynb`) are thin wrappers over `src/` modules.
`data/demo/` contains placeholder personal demo cases (display only, never in any
split, never published).

## Dataset card & versioning

See `DATASET_CARD.md` (fields, collection, audits, maintenance policy) and
`data/processed/DATASET_META.json` (version + changelog + canary GUID).
Canary: `lifeevent-cp CANARY 98669f31-33e2-4591-8cc9-96ac3b1afa16` (BIG-bench
convention — detection aid for benchmark contamination, not a defense).

**Changelog**: 0.1 dry-run (2026-08-03) → 0.2 full 500 questions (2026-08-03; audit
caught Wikidata genid unknown-value labels, 21/500 affected) → **0.3 rebuild**
(2026-08-04; genid/URL filter, label-echo rule, generic-label filter, era band,
path isolation; implausible-distractor share 42%→18% across three audit rounds).

**Evaluation-setting note** (temporal-KG terminology): our negative legality is
stricter than a static filter, and the same-person wrong-time distractor is a legal
negative under time-aware filtering conventions — scores are not comparable to
raw-setting KG leaderboards.

## Limitations

See `reports/中文结果报告.md` (Chinese result report) — includes dataset skew
(position-holders dominate timed statements), entity-level candidate-pool sharing
across splits, small-n coverage noise, contamination quantification (nameless-timeline
name-cloze probe + guided ablation), and the conservative quantile implementation note.
