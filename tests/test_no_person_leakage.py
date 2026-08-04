"""Spec test 1 + adopted E-2 guards: split disjointness, person-name exclusion from
model input, TF-IDF vocabulary built from train texts only."""

from __future__ import annotations

from src.split_people import events_by_person
from src.text_features import fit_vectorizer, question_records, render_record
from src.utils import PROJECT_ROOT, read_json, read_jsonl

REAL_SPLIT = PROJECT_ROOT / "data" / "processed" / "person_split.json"
REAL_Q = PROJECT_ROOT / "data" / "processed" / "life_event_questions.json"


def test_split_persons_disjoint(built):  # spec test 1
    per_split: dict[str, set] = {"train": set(), "calibration": set(), "test": set()}
    for q in built["questions"]:
        per_split[q["split"]].add(q["person_id"])
    assert not per_split["train"] & per_split["calibration"]
    assert not per_split["train"] & per_split["test"]
    assert not per_split["calibration"] & per_split["test"]
    if REAL_Q.exists():
        real: dict[str, set] = {"train": set(), "calibration": set(), "test": set()}
        for q in read_json(REAL_Q):
            real[q["split"]].add(q["person_id"])
        assert not real["train"] & real["calibration"]
        assert not real["train"] & real["test"]
        assert not real["calibration"] & real["test"]
        if REAL_SPLIT.exists():
            assignment = read_json(REAL_SPLIT)
            for split, persons in real.items():
                assert all(assignment[p] == split for p in persons)


def test_person_name_not_in_model_input(built):
    """person_label must never be rendered into any model input text."""
    for q in built["questions"]:
        tokens = set(q["person_label"].split())
        for c in q["candidates"]:
            text = render_record(q, c["text"])
            assert not (tokens & set(text.split())), q["question_id"]
    # synthetic labels are 'ZzgivenNNN ZzfamilyNNN' — assert the distinctive stem too
    for q in built["questions"]:
        for _, _, text, _ in question_records(q):
            assert "Zzgiven" not in text and "Zzfamily" not in text


def test_tfidf_fitted_on_train_only(config, built):  # adopted E-2
    train_texts, other_texts = [], []
    for q in built["questions"]:
        target = train_texts if q["split"] == "train" else other_texts
        target.extend(text for _, _, text, _ in question_records(q))
    canary = "zzcanaryleakzz"
    other_texts = [t + f"\n{canary} {canary}" for t in other_texts]  # twice: beats min_df=2
    vec = fit_vectorizer(config, train_texts)
    assert canary not in vec.vocabulary_
    assert all(canary not in feat for feat in vec.vocabulary_)
