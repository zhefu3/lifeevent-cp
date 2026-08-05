---
license: cc0-1.0
task_categories: [multiple-choice]
language: [en]
tags: [conformal-prediction, wikidata, temporal-knowledge, uncertainty-quantification]
pretty_name: LifeEvent-CP
size_categories: [n<1K]
---

# Dataset Card: LifeEvent-CP v0.3

`lifeevent-cp CANARY 98669f31-33e2-4591-8cc9-96ac3b1afa16` — canary GUID for contamination detection (BIG-bench convention). Its presence in a trained model indicates this benchmark leaked into training data. The canary is a detection aid, not a defense.

## Dataset summary

500 six-way multiple-choice questions. Each question gives a partial, year-stamped
timeline of a public figure (name removed; ≤2 events before + ≤2 after a hidden middle
year) and asks which of 6 candidate events is the one recorded for the hidden year in
Wikidata. Ground truth is the held-out Wikidata statement — explicitly NOT "the only
event a real life could contain".

- **Splits**: train 300 / calibration 100 / test 100, person-disjoint (a person never
  crosses splits), exactly 1 question per person, all randomness from seed 42.
- **Distractor recipe** per question: 2 same-type near-year + 1 label-similar same-type
  + 1 same-person wrong-time (fallback: near-year) + 1 same-type random (era band ±60y).
- **Filtered-setting note** (temporal-KG terminology): negative legality is stricter
  than a static filter — negatives must not appear anywhere in the person's harvested
  event table (except the deliberate same-person type, which is legal under time-aware
  filtering conventions). Scores are NOT comparable to raw-setting KG leaderboards.

## Data fields (life_event_questions.json)

| field | type | description |
|---|---|---|
| question_id | str | `{person_qid}_{missing_year}_{property}` |
| person_id / person_label | str | Wikidata QID / English label (display only — never in model input) |
| observed_events[] | list | year, event_type, target_id, target_label, text |
| missing_year | int | the hidden year |
| candidates[] | list | candidate_id A–F, event_type, target_id, target_label, text, distractor_type |
| correct_candidate_id | str | letter of the held-out statement |
| hidden_event_type / hidden_target_id | str | metadata of the hidden statement |
| split | str | train / calibration / test |

## Collection process

Two-phase SPARQL harvest (2026-08-03/04 snapshot): (1) discovery per
(property × time-qualifier × year-slice) with adaptive slice splitting, 345,778 timed
persons found; (2) complete timed statements (P69/P108/P39/P166, qualifiers P580/P585)
for a per-type-balanced pool of 4,387 persons. Cleaning: year int cast, missing/QID/URL
(genid) label drop, dedupe, 1850–2026 range. All raw responses cached (data/raw/,
excluded from the repo); the dataset is reproducible from cache without network.

## Quality control

Three audit rounds (150 questions total, five independent reviewers + adversarial
re-check per round): 50/50 pass on leakage/uniqueness/ground-truth-validity/timeline
coherence in the final round; implausible-distractor share reduced 42%→18% across
rounds; residual "second plausible answer" rate disclosed (~25/50 POSSIBLE, concentrated
in same-person wrong-time distractors and repeatable awards — an intrinsic tension of
KG incompleteness, disclosed rather than hidden).

## Maintenance

Frozen per version (see changelog in `data/processed/DATASET_META.json`); Wikidata is a
living database, so fixes ship only as whole-version rebuilds with re-audit. Known
limitations: public-figure skew (positions/awards dominate), English labels only,
year-level time precision, no end-time (P582) intervals in v0.3.

## License & privacy

Source data: Wikidata, CC0. All persons are public figures; the personal-demo directory
(private placeholder) never enters this repository.
