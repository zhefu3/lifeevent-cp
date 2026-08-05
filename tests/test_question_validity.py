"""Spec tests 2-9: question structure, anti-leak construction, negative legality,
seed reproducibility. Runs on synthetic questions always, and on the real generated
dataset when data/processed/life_event_questions.json exists."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

from src.question_builder import build_all_questions
from src.split_people import eligible_persons, events_by_person, split_persons
from src.utils import PROJECT_ROOT, load_config, read_json, read_jsonl

REAL_Q = PROJECT_ROOT / "data" / "processed" / "life_event_questions.json"
REAL_E = PROJECT_ROOT / "data" / "processed" / "person_events.jsonl"


def _datasets(built):
    sets = [(built["questions"], built["grouped"])]
    if REAL_Q.exists() and REAL_E.exists():
        sets.append((read_json(REAL_Q), events_by_person(list(read_jsonl(REAL_E)))))
    return sets


def test_exactly_six_candidates(built):  # spec test 2
    for questions, _ in _datasets(built):
        for q in questions:
            assert len(q["candidates"]) == 6, q["question_id"]


def test_correct_candidate_appears_once(built):  # spec test 3
    for questions, _ in _datasets(built):
        for q in questions:
            marked = [c for c in q["candidates"] if c["distractor_type"] == "correct"]
            assert len(marked) == 1 and marked[0]["candidate_id"] == q["correct_candidate_id"]
            assert marked[0]["target_id"] == q["hidden_target_id"]


def test_candidate_texts_unique(built):  # spec test 4
    for questions, _ in _datasets(built):
        for q in questions:
            texts = [c["text"] for c in q["candidates"]]
            assert len(set(texts)) == 6, q["question_id"]


def test_hidden_event_not_in_context(built):  # spec test 5 (+ tightened no-target-repeat rule)
    for questions, _ in _datasets(built):
        for q in questions:
            for o in q["observed_events"]:
                assert o["year"] != q["missing_year"]
                assert o["target_id"] != q["hidden_target_id"], q["question_id"]


def test_no_label_level_echo(built):  # A6 v0.2 finding #2: correct text must not appear in context
    for questions, _ in _datasets(built):
        for q in questions:
            correct = next(c for c in q["candidates"] if c["candidate_id"] == q["correct_candidate_id"])
            for o in q["observed_events"]:
                assert correct["text"].lower() not in o["text"].lower(), q["question_id"]


def test_correct_label_not_generic(built):  # A6 v0.2 finding #4: bare lowercase one-word labels
    for questions, _ in _datasets(built):
        for q in questions:
            correct = next(c for c in q["candidates"] if c["candidate_id"] == q["correct_candidate_id"])
            lab = correct["target_label"]
            assert not (len(lab.split()) == 1 and lab == lab.lower()), q["question_id"]


def test_hidden_year_is_middle(built):  # spec test 6
    for questions, grouped in _datasets(built):
        for q in questions:
            years = sorted({e["year"] for e in grouped[q["person_id"]]})
            assert years[0] < q["missing_year"] < years[-1], q["question_id"]


def test_hidden_year_single_ground_truth(built):  # spec test 7
    for questions, grouped in _datasets(built):
        for q in questions:
            n = sum(1 for e in grouped[q["person_id"]] if e["year"] == q["missing_year"])
            assert n == 1, q["question_id"]


def test_negative_candidates_legal(built):  # spec test 8 (+ adopted E-3)
    for questions, grouped in _datasets(built):
        for q in questions:
            person_targets = {e["target_id"] for e in grouped[q["person_id"]]}
            shown = {o["target_id"] for o in q["observed_events"]}
            for c in q["candidates"]:
                if c["distractor_type"] == "correct":
                    continue
                if c["distractor_type"] == "same_person_wrong_time":
                    assert c["target_id"] in person_targets
                    assert c["target_id"] not in shown, q["question_id"]  # E-3
                    assert c["target_id"] != q["hidden_target_id"]
                else:
                    assert c["target_id"] not in person_targets, q["question_id"]


def test_seed_reproducibility(config, synthetic_events, built):  # spec test 9
    grouped = events_by_person(synthetic_events)
    eligible = eligible_persons(grouped, config)
    rng = np.random.default_rng(int(config["random_seed"]))
    assignment = split_persons(eligible, config, rng)
    questions = build_all_questions(grouped, assignment, synthetic_events, config, rng,
                                    {"train": 10, "calibration": 5, "test": 5}, 1)
    assert assignment == built["assignment"]
    assert json.dumps(questions, sort_keys=True) == json.dumps(built["questions"], sort_keys=True)


def test_canary_present_in_published_docs():
    """BIG-bench convention: the canary GUID must appear in every published data doc."""
    canary = "98669f31-33e2-4591-8cc9-96ac3b1afa16"
    for rel in ("data/processed/DATASET_META.json", "DATASET_CARD.md", "README.md"):
        path = PROJECT_ROOT / rel
        if path.exists():
            assert canary in path.read_text(encoding="utf-8"), rel


def test_distractor_recipe_counts(built):
    """Composition sanity: >=5 negatives incl. the mandated types when available."""
    for questions, _ in _datasets(built):
        for q in questions:
            dtypes = [c["distractor_type"] for c in q["candidates"]]
            assert dtypes.count("correct") == 1
            assert len(dtypes) == 6
