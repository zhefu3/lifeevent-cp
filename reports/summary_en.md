# LifeEvent-CP: Conformal Prediction over Masked Wikidata Life Events

*One-page summary. Code & data: https://github.com/zhefu3/lifeevent-cp (CC0 Wikidata source data; fully reproducible on a laptop CPU, all randomness seeded).*

## Task

Following your advice, I shrank the open-ended "life modeling" idea into a sharply defined prediction task: given a partial, year-stamped timeline of a public figure from Wikidata (person name removed, at most 2 events before and 2 after), one middle-year event is hidden; the model scores 6 candidates (1 correct + 5 typed distractors) and outputs split conformal prediction sets at 80/90/95% target coverage. Ground truth is the held-out Wikidata statement — no claim about "the only event a real life could contain".

**Dataset**: 345,778 timed persons discovered → 500 questions (300 train / 100 calibration / 100 test), person-disjoint splits, seed-fixed. Three manual audit rounds (150 questions total) caught and fixed real defects (Wikidata unknown-value genid labels; era-mismatched distractors — implausible distractor share cut from 42% to 18%).

## Results

| test = 100 | TF-IDF + LogReg | LLM (6-way scoring) |
|---|---|---|
| Point accuracy (random = 0.167) | 0.14 | **0.68** |
| Empirical coverage @0.80/0.90/0.95 | 0.83 / 0.91 / 0.97 | 0.78 / 0.93 / 0.97 |
| Avg. set size @0.80/0.90/0.95 | 4.42 / 4.86 / 5.53 | **1.45 / 2.35 / 3.67** |
| Singleton rate @0.80 | 0.00 | 0.54 |
| ECE (10-bin) | 0.043 | 0.185 (overconfident) |

1. **Coverage holds for both models** — all six empirical coverages fall inside their Wilson 95% intervals. **Set size is an honest ruler of discriminative power**: the same 90% guarantee costs a near-random model 4.86 candidates but the LLM only 2.35.
2. **Contamination is quantified, not hand-waved**: a name-cloze-style probe (cf. Chang et al. 2023) over all 100 test questions identifies the person 31% of the time (accuracy 0.742 identified vs 0.652 unidentified); a **guided ablation** (same questions with the name revealed, cf. Time-Travel ICLR 2024) lifts accuracy 0.68 → 0.78 (McNemar p = 0.064) — causal evidence that the memorization channel is worth ~10 points, while the unidentified-subset 0.652 stays ~4x random. Half of the LLM's errors pick the *same-person wrong-time* distractor (~4x other types): it wins on knowing the person and loses on the temporal boundary of that knowledge. Elicitation follows the verbalized-probability recommendation for RLHF models (Tian et al. 2023; text-answer parsing per Wang et al. 2024); a letter-consistency audit gives 0.70 overall / 0.82 on high-margin questions.
3. **Shift breaks the guarantee in both directions** (deliberate exchangeability violations, reusing existing scores): era-shifted calibration under-covers (TF-IDF @0.95 drops to 0.80, Wilson interval excludes the target), while calibrating on a harder subgroup wastes efficiency (sets inflate to near-full at unchanged nominal level). Mondrian (per-type) calibration evens group coverage at a set-size cost driven by small per-group calibration n.
4. **Self-reflection makes the LLM more confident, not more accurate** (v2): accuracy 0.68 → 0.67 while mean max-probability rises 0.498 → 0.539 and 46/200 answers switch. The sharpened scores do buy conformal efficiency (avg set @0.95: 3.67 → 2.86 at unchanged coverage) — confidence without accuracy is not entirely wasted, but it is not understanding either.

5. **Method extras** (same scores, no new calls): randomized APS matches LAC tightly (0.90 coverage, 2.32 avg set for the LLM) where the conservative variant degenerates; Mondrian per-type calibration equalizes group coverage at a set-size cost; a calibration-size study shows the 90% guarantee spans [0.86, 1.00] (TF-IDF) / [0.85, 1.00] (LLM) empirical coverage when n_cal = 20.

6. **Standard-practice alignment** (adopted from a survey of MAPIE/TorchCP/crepes/A&B, LLM-Uncertainty-Bench, TKG benchmarks, and benchmark-engineering conventions): SSC + singleton-hit-rate + UAcc + popularity-stratified reporting; a frequency-prior baseline scores 0.18 ≈ random (the answer prior gives nothing away); conformal p-value KS uniformity passes for TF-IDF (p = 0.097) but flags the LLM channel (p = 0.003) despite nominal coverage holding — an honest open diagnostic; across R = 100 person-level resplits the mean empirical coverage falls inside the analytic Beta(n+1−l, l) band at every level (the empirical 5–95 bands run slightly wider than theory at both ends); PRR 0.54 (rejecting the most-uncertain half lifts accuracy 0.68 → 0.84); answer-letter chi-square shows no selection bias; dataset card, versioning + changelog, and a BIG-bench canary GUID ship with the repo.

## Scope & limitations (highlights)

Marginal coverage only, under person-level exchangeability; public-figure skew (positions/awards dominate); Wikidata incompleteness (absence of a statement is not absence of an event — audited "second plausible answer" rate disclosed); n=100 calibration/test noise quantified throughout; LAC quantile uses the standard tutorial recipe (conservative by ≤1 order statistic).



## Next

Larger calibration/test sets to tighten intervals, model-tier comparison under the identical harness, and method work targeted at the observed failure modes (temporal-boundary errors, contamination-aware evaluation) rather than a priori algorithm design.
