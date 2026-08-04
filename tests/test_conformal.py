"""Spec tests 10-12: quantile computed from calibration only, test split untouched by
any selection, and hand-worked unit examples for the conformal/coverage logic."""

from __future__ import annotations

import numpy as np
import pytest

from src.conformal import (attach_sets, calibration_scores, fit_all_qhats, fit_qhat,
                           prediction_set, quantile_level)
from src.evaluate import evaluate, wilson_ci
from src.utils import PROJECT_ROOT, read_json, read_jsonl

QHATS = PROJECT_ROOT / "outputs" / "qhats.json"
PREDS = PROJECT_ROOT / "outputs" / "predictions.jsonl"


def test_quantile_hand_example():  # spec test 12 (quantile part)
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    assert quantile_level(10, 0.20) == pytest.approx(0.9)
    # np.quantile(..., 0.9, method="higher") on 10 sorted values -> index ceil(0.9*9)=9
    assert fit_qhat(scores, 0.20) == pytest.approx(1.0)
    assert quantile_level(10, 0.50) == pytest.approx(0.6)
    assert fit_qhat(scores, 0.50) == pytest.approx(0.7)
    # n large enough that level < 1
    scores100 = np.linspace(0.005, 1.0, 100)
    assert quantile_level(100, 0.10) == pytest.approx(0.91)


def test_prediction_set_logic():  # spec test 12 (set part)
    scores = {"A": 0.5, "B": 0.3, "C": 0.15, "D": 0.05}
    assert prediction_set(scores, 0.60) == ["A"]          # 1-p: A .5<=.6
    assert prediction_set(scores, 0.75) == ["A", "B"]
    assert prediction_set(scores, 0.40) == []              # empty set allowed
    assert prediction_set(scores, 1.00) == ["A", "B", "C", "D"]


def test_calibration_scores_from_correct_candidate():
    preds = [{"candidate_scores": {"A": 0.7, "B": 0.3}, "correct_candidate_id": "A"},
             {"candidate_scores": {"A": 0.2, "B": 0.8}, "correct_candidate_id": "A"}]
    s = calibration_scores(preds)
    assert s.tolist() == pytest.approx([0.3, 0.8])


def test_coverage_logic_hand_example(tmp_path):  # spec test 12 (coverage part)
    questions, preds = [], []
    truth_sets = {"q1": ["A"], "q2": ["A", "B"], "q3": [], "q4": ["B"]}
    correct = {"q1": "A", "q2": "B", "q3": "A", "q4": "C"}
    for qid in truth_sets:
        cands = []
        for cid in "ABCDEF":
            cands.append({"candidate_id": cid, "event_type": "education", "target_id": f"T{cid}",
                          "target_label": f"L{cid}", "text": f"text {qid} {cid}",
                          "distractor_type": "correct" if cid == correct[qid] else "same_type_random"})
        questions.append({"question_id": qid, "person_id": f"P{qid}", "person_label": "X",
                          "observed_events": [], "missing_year": 2000, "candidates": cands,
                          "correct_candidate_id": correct[qid], "hidden_event_type": "education",
                          "hidden_target_id": f"T{correct[qid]}", "source": "synthetic", "split": "test"})
        scores = {cid: (0.5 if cid == "A" else 0.1) for cid in "ABCDEF"}
        preds.append({"question_id": qid, "split": "test", "candidate_scores": scores,
                      "point_prediction": "A", "correct_candidate_id": correct[qid],
                      "conformal_sets": {"0.90": truth_sets[qid]}})
    summary = evaluate(questions, preds, tmp_path)
    # covered: q1 (A in {A}), q2 (B in {A,B}); q3 empty set, q4 C not in {B} -> 2/4
    overall = [r for r in summary["coverage_overall"] if r["coverage_target"] == "0.90"][0]
    assert overall["empirical_coverage"] == pytest.approx(0.5)
    assert overall["empty_set_rate"] == pytest.approx(0.25)
    assert summary["point_accuracy"] == pytest.approx(0.5)  # q1, q3 correct (point always A)


def test_wilson_ci_sanity():
    lo, hi = wilson_ci(90, 100)
    assert 0.82 < lo < 0.87 and 0.93 < hi < 0.96


def test_qhat_derived_from_calibration_only():  # spec tests 10 & 11 (integration)
    if not (QHATS.exists() and PREDS.exists()):
        pytest.skip("no real pipeline outputs yet")
    stored = read_json(QHATS)
    preds = list(read_jsonl(PREDS))
    cal = [p for p in preds if p["split"] == "calibration"]
    assert stored["n_calibration"] == len(cal)
    recomputed = fit_all_qhats(calibration_scores(cal), [0.20, 0.10, 0.05])
    for cov, q in recomputed.items():
        assert stored["q_hats"][cov] == pytest.approx(q)
    # test rows only received sets; verify sets are pure threshold functions of stored q_hats
    for p in [p for p in preds if p["split"] == "test"][:50]:
        for cov, q in stored["q_hats"].items():
            assert p["conformal_sets"][cov] == prediction_set(p["candidate_scores"], q)
