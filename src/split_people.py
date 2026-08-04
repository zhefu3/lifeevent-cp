"""Person-level eligibility filter and the train/calibration/test split.

The split is over PERSONS (60/20/20), decided before any question is generated, so a
person's questions can never straddle splits. Deterministic under random_seed.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from .utils import setup_logging

LOG = setup_logging()


def events_by_person(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in events:
        grouped[ev["person_id"]].append(ev)
    for pid in grouped:
        grouped[pid].sort(key=lambda r: (r["year"], r["property_id"], r["target_id"]))
    return dict(grouped)


def hideable_years(person_events: list[dict[str, Any]]) -> list[int]:
    """Years eligible for hiding: strictly between the person's first and last event
    year AND carrying exactly one event (unique ground truth)."""
    years = sorted({ev["year"] for ev in person_events})
    if len(years) < 3:
        return []
    per_year: dict[int, int] = defaultdict(int)
    for ev in person_events:
        per_year[ev["year"]] += 1
    return [y for y in years[1:-1] if per_year[y] == 1]


def eligible_persons(grouped: dict[str, list[dict[str, Any]]], config: dict[str, Any]) -> list[str]:
    """Persons with >= min_distinct_years distinct event years and >=1 hideable year."""
    need = int(config["person_filters"]["min_distinct_years"])
    keep = [pid for pid, evs in grouped.items()
            if len({e["year"] for e in evs}) >= need and hideable_years(evs)]
    LOG.info("eligibility: %d/%d persons pass (>=%d distinct years + hideable middle)",
             len(keep), len(grouped), need)
    return sorted(keep)


def split_persons(person_ids: list[str], config: dict[str, Any], rng: np.random.Generator) -> dict[str, str]:
    """Shuffle persons and cut 60/20/20. Returns person_id -> split name."""
    ids = sorted(person_ids)
    order = rng.permutation(len(ids))
    shuffled = [ids[i] for i in order]
    n = len(shuffled)
    n_train = int(round(n * float(config["split"]["train"])))
    n_cal = int(round(n * float(config["split"]["calibration"])))
    assignment: dict[str, str] = {}
    for i, pid in enumerate(shuffled):
        if i < n_train:
            assignment[pid] = "train"
        elif i < n_train + n_cal:
            assignment[pid] = "calibration"
        else:
            assignment[pid] = "test"
    counts = {s: sum(1 for v in assignment.values() if v == s) for s in ("train", "calibration", "test")}
    LOG.info("person split: %s", counts)
    return assignment
