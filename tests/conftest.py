"""Shared fixtures: config, synthetic normalized events, built questions (offline)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.question_builder import build_all_questions  # noqa: E402
from src.split_people import eligible_persons, events_by_person, split_persons  # noqa: E402
from src.utils import load_config  # noqa: E402

TYPES = [("education", "P69"), ("employment", "P108"), ("position", "P39"), ("award", "P166")]


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def synthetic_events(config):
    """40 persons x 6 events (distinct years, distinct targets) in normalized schema."""
    events = []
    for i in range(40):
        pid = f"Q9{i:03d}"
        base = 1990 + (i % 5)
        for k in range(6):
            etype, prop = TYPES[(i + k) % 4]
            tid = f"Q5{((i * 6 + k) % 80):03d}{['E', 'W', 'P', 'A'][(i + k) % 4]}"
            label = f"{etype.capitalize()} Target {((i * 6 + k) % 80):03d}"
            year = base + 3 * k
            template = config["event_types"][etype]["template"]
            events.append({
                "person_id": pid, "person_label": f"Zzgiven{i:03d} Zzfamily{i:03d}",
                "property_id": prop, "event_type": etype,
                "target_id": tid, "target_label": label, "year": year,
                "time_source": "P580", "statement_uri": f"wds:{pid}-{k}",
                "event_text": f"{year}: " + template.format(target=label),
            })
    return events


@pytest.fixture(scope="session")
def built(config, synthetic_events):
    """Deterministic end-to-end build over the synthetic table."""
    grouped = events_by_person(synthetic_events)
    eligible = eligible_persons(grouped, config)
    rng = np.random.default_rng(int(config["random_seed"]))
    assignment = split_persons(eligible, config, rng)
    questions = build_all_questions(grouped, assignment, synthetic_events, config, rng,
                                    {"train": 10, "calibration": 5, "test": 5}, 1)
    return {"grouped": grouped, "assignment": assignment, "questions": questions}
