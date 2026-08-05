# LifeEvent-CP: Conformal Prediction over Masked Wikidata Life Events

*One-page summary, dataset v0.4. Code & data: https://github.com/zhefu3/lifeevent-cp (MIT code / CC0 data; reproducible on a laptop CPU, all randomness seeded, SPARQL responses cached).*

## Task

A sharply defined slice of the "life modeling" idea: given a partial, year-stamped timeline of a public figure from Wikidata (name removed, ≤2 events before + ≤2 after), one middle-year event is hidden; models score 6 candidates and output split conformal prediction sets at 80/90/95% target coverage. Ground truth is the held-out Wikidata statement.

**Dataset v0.4** (four audit rounds, 200 questions reviewed in total): 345,778 timed persons discovered → 500 questions, person-disjoint splits. v0.4 adopts TempLAMA-style interval facts (P582 end-times; a same-person distractor whose tenure covers the missing year is illegal) and TGB-2.0-style negative legality (undated true statements cannot serve as negatives) — cutting the audited second-plausible-answer rate from 25+2/50 to **6+0/50**. The benchmark got harder *and* cleaner: the LLM dropped from 0.68 (v0.3) to 0.57 — measurement got more accurate, not the model worse.

## Results (test = 100)

| | TF-IDF | LLM (verbalized 6-way) | frequency prior |
|---|---|---|---|
| Point accuracy (random .167) | 0.14 | **0.57** | 0.20 |
| Top-2 accuracy | 0.38 | **0.82** | — |
| Coverage @.80/.90/.95 | .72/.87/.98 | .81/.93/.93 | — |
| Avg set size @.80/.90/.95 | 3.80/4.87/5.54 | **1.75/2.54/2.71** | — |
| Singleton rate (hit-rate) @.90 | 0 (—) | **.18 (.94)** | — |
| UAcc @.90 / PRR | .070 / −.07 | **.550 / .66** | — |

1. **Coverage holds and survives theory-checking**: across R = 100 person-level resplits, mean empirical coverage falls inside the analytic Beta(n+1−l, l) band at every level for both models (one raw draw shows TF-IDF @.80 marginally under; the resplit protocol is the stable read).
2. **Set size is an honest ruler**: the same 90% guarantee costs the near-random model 4.87 candidates and the LLM 2.54; singleton sets are right 94% of the time; rejecting the most-uncertain half lifts LLM accuracy 0.57 → 0.80.
3. **Contamination is pinned down by a three-layer evidence chain**: name-cloze probe identifies 41% of persons from nameless timelines; identified vs unidentified accuracy 0.707 vs 0.475; guided ablation (name revealed) lifts accuracy +0.16 (McNemar p = 0.009); and the conformal p-value distributions of identified vs unidentified questions differ significantly (two-sample KS p = 0.0007) — **contamination distorts the uncertainty structure itself, not just accuracy**. Consistently, LLM errors concentrate 5x on same-person wrong-time distractors: it wins on knowing the person, loses on the temporal boundary of that knowledge.
4. **Self-reflection (v0.3-era experiment)** made the model more confident (0.498→0.539), not more accurate (0.68→0.67), though sharper scores bought set-size efficiency at 95%.
5. **Method extras**: randomized APS removes the conservative variant's over-coverage; Mondrian equalizes per-type coverage at a set-size cost; a frequency-prior baseline scores 0.20 ≈ random (the answer prior gives nothing away); answer-letter chi-square is uniform for TF-IDF but flags mild E/F selection bias for the LLM on v0.4 (p = 0.010; uniform on v0.3 — reported, debiasing left as future work); with n_cal = 20 the "90%" guarantee spans empirical coverage up to [0.81, 1.00].

Elicitation follows verbalized-probability practice for RLHF models (Tian et al. 2023; text answers per Wang et al. 2024); letter-consistency audit 0.66 reported as an interpretive bound. Min-K%-style logprob detectors are unavailable over the CLI channel (disclosed).

## Scope & limitations

Marginal coverage under person-level exchangeability; public-figure skew; Wikidata incompleteness (residual multi-answer rate audited and disclosed); n = 100 noise quantified throughout; KS-uniformity diagnostics drift across dataset versions at this n (reported as open diagnostics); LLM outputs cached for reproducibility.

## Next

Method work grows out of the observed failure modes: temporal-boundary errors, contamination-stratified evaluation, larger calibration sets, model-tier comparison under the identical harness.
