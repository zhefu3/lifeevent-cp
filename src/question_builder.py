"""Question generation: hide one middle event, build 6 candidates with typed distractors.

Distractor recipe per question (spec):
  1 correct + 2 same_type_near_year + 1 label_similar_same_type
  + 1 same_person_wrong_time (fallback: near-year same type) + 1 same_type_random.

Legality rules:
- negative targets must NOT appear anywhere in the person's complete event table,
  except the deliberate same_person_wrong_time candidate;
- E-3 (adopted): the same_person_wrong_time candidate must not appear among the
  DISPLAYED observed_events, its year must differ from missing_year and its target
  from the correct target;
- all candidate texts unique; exactly one correct candidate; order shuffled (seeded).

Pools are built from the full normalized event table (entity-level sharing across
splits; persons never cross splits — documented in limitations).
"""

from __future__ import annotations

import difflib
from collections import defaultdict
from typing import Any

import numpy as np

from .split_people import hideable_years
from .utils import setup_logging

LOG = setup_logging()

LETTERS = ["A", "B", "C", "D", "E", "F"]


def is_generic_label(label: str) -> bool:
    """Bare all-lowercase single-token labels ('member', 'chairperson') carry almost no
    signal as candidates; proper-noun short names (RTVE, Siemens) keep capitals and pass.
    (A6 v0.2 finding #4.)"""
    return len(label.split()) == 1 and label == label.lower()


class CandidatePools:
    """Per-event-type pools over the full event table, plus per-person target sets.
    Generic bare labels are excluded from distractor pools (not from person timelines)."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self.by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.person_targets: dict[str, set[str]] = defaultdict(set)
        seen: set[tuple[str, str, int]] = set()
        for ev in sorted(events, key=lambda r: (r["event_type"], r["target_id"], r["year"], r["person_id"])):
            self.person_targets[ev["person_id"]].add(ev["target_id"])
            if is_generic_label(ev["target_label"]):
                continue
            key = (ev["event_type"], ev["target_id"], ev["year"])
            if key not in seen:  # one pool entry per (type, target, year)
                seen.add(key)
                self.by_type[ev["event_type"]].append(ev)
        self.labels_by_type: dict[str, list[tuple[str, str]]] = {
            t: sorted({(e["target_id"], e["target_label"]) for e in rows})
            for t, rows in self.by_type.items()
        }


def _cand_text(ev: dict[str, Any], config: dict[str, Any]) -> str:
    template = config["event_types"][ev["event_type"]]["template"]
    return template.format(target=ev["target_label"])


def _mk_candidate(ev: dict[str, Any], dtype: str, config: dict[str, Any]) -> dict[str, Any]:
    return {"event_type": ev["event_type"], "target_id": ev["target_id"],
            "target_label": ev["target_label"], "text": _cand_text(ev, config),
            "distractor_type": dtype, "source_year": ev["year"]}


def _legal_negative(ev: dict[str, Any], person_id: str, pools: CandidatePools,
                    correct_target: str, used_texts: set[str], text: str) -> bool:
    return (ev["target_id"] != correct_target
            and ev["target_id"] not in pools.person_targets[person_id]
            and text not in used_texts)


def _pick_near_year(etype: str, missing_year: int, person_id: str, pools: CandidatePools,
                    correct_target: str, used_texts: set[str], config: dict[str, Any],
                    rng: np.random.Generator, dtype: str) -> dict[str, Any] | None:
    for w in config["question"]["near_year_windows"]:
        pool = [e for e in pools.by_type.get(etype, [])
                if abs(e["year"] - missing_year) <= w
                and _legal_negative(e, person_id, pools, correct_target, used_texts, _cand_text(e, config))]
        if pool:
            return _mk_candidate(pool[int(rng.integers(len(pool)))], dtype, config)
    return None


def _pick_random(etype: str, person_id: str, pools: CandidatePools, correct_target: str,
                 used_texts: set[str], config: dict[str, Any], rng: np.random.Generator,
                 missing_year: int | None = None) -> dict[str, Any] | None:
    """Random same-type negative, era-banded when missing_year is given (audit round 1
    found e.g. WNBA awards offered for 19th-century statesmen — random stays random but
    within a wide era window)."""
    band = int(config["question"].get("era_band_random", 10000))
    pool = [e for e in pools.by_type.get(etype, [])
            if (missing_year is None or abs(e["year"] - missing_year) <= band)
            and _legal_negative(e, person_id, pools, correct_target, used_texts, _cand_text(e, config))]
    if pool:
        return _mk_candidate(pool[int(rng.integers(len(pool)))], "same_type_random", config)
    return None


def _pick_label_similar(etype: str, correct_label: str, person_id: str, pools: CandidatePools,
                        correct_target: str, used_texts: set[str],
                        config: dict[str, Any]) -> dict[str, Any] | None:
    """Deterministic: rank a bounded same-type label subset by difflib ratio."""
    labels = pools.labels_by_type.get(etype, [])
    if not labels:
        return None
    tokens = {t.lower() for t in correct_label.split()}
    sharers = [(tid, lab) for tid, lab in labels if tokens & {w.lower() for w in lab.split()}]
    stride = max(1, len(labels) // 2000)
    subset = {(tid, lab) for tid, lab in sharers[:2000]} | set(labels[::stride])
    ranked = sorted(subset,  # tid as final tie-break: same-label ties must not fall back to set hash order (A6 finding)
                    key=lambda p: (-difflib.SequenceMatcher(None, correct_label.lower(), p[1].lower()).ratio(), p[1], p[0]))
    template = config["event_types"][etype]["template"]
    for tid, lab in ranked:
        text = template.format(target=lab)
        if (tid != correct_target and tid not in pools.person_targets[person_id]
                and text not in used_texts and lab != correct_label):
            return {"event_type": etype, "target_id": tid, "target_label": lab, "text": text,
                    "distractor_type": "label_similar_same_type", "source_year": None}
    return None


def _pick_same_person(person_events: list[dict[str, Any]], observed: list[dict[str, Any]],
                      missing_year: int, correct_target: str, used_texts: set[str],
                      config: dict[str, Any], rng: np.random.Generator) -> dict[str, Any] | None:
    """Deliberate same-person wrong-time negative under E-3 constraints."""
    shown_targets = {o["target_id"] for o in observed}
    pool = []
    for ev in person_events:
        text = _cand_text(ev, config)
        if (ev["year"] != missing_year and ev["target_id"] != correct_target
                and ev["target_id"] not in shown_targets and text not in used_texts):
            pool.append(ev)
    if pool:
        return _mk_candidate(pool[int(rng.integers(len(pool)))], "same_person_wrong_time", config)
    return None


def build_question(person_id: str, person_events: list[dict[str, Any]], missing_year: int,
                   pools: CandidatePools, config: dict[str, Any], rng: np.random.Generator,
                   split: str) -> dict[str, Any] | None:
    """Assemble one question for (person, missing_year); None when <5 legal negatives."""
    hidden = [e for e in person_events if e["year"] == missing_year]
    if len(hidden) != 1:
        return None
    hidden_ev = hidden[0]
    before = [e for e in person_events if e["year"] < missing_year][-int(config["question"]["context_before"]):]
    after = [e for e in person_events if e["year"] > missing_year][:int(config["question"]["context_after"])]
    observed = [{"year": e["year"], "event_type": e["event_type"], "target_id": e["target_id"],
                 "target_label": e["target_label"], "text": e["event_text"]} for e in before + after]
    # Tightened rule (A4, mirrors adopted E-3): the hidden target must not appear in the
    # DISPLAYED context at any year (e.g. re-elected positions), else the candidate text
    # trivially matches a context line and the answer is half-leaked.
    if hidden_ev["target_id"] in {o["target_id"] for o in observed}:
        return None
    # Label-level echo (A6 v0.2 finding #2, same family as genid: one value, many
    # representations): same-name-different-QID entities and bare-prefix labels slip the
    # target_id rule, so also reject when the correct candidate text appears as a
    # substring of any displayed context line.
    correct_text = _cand_text(hidden_ev, config).lower()
    if any(correct_text in o["text"].lower() for o in observed):
        return None
    # Generic bare correct labels make near-unanswerable questions (A6 finding #4).
    if is_generic_label(hidden_ev["target_label"]):
        return None

    etype, correct_target = hidden_ev["event_type"], hidden_ev["target_id"]
    correct = _mk_candidate(hidden_ev, "correct", config)
    used_texts = {correct["text"]}
    negatives: list[dict[str, Any]] = []

    def _add(cand: dict[str, Any] | None) -> bool:
        if cand is None:
            return False
        negatives.append(cand)
        used_texts.add(cand["text"])
        return True

    for _ in range(2):
        _add(_pick_near_year(etype, missing_year, person_id, pools, correct_target,
                             used_texts, config, rng, "same_type_near_year"))
    _add(_pick_label_similar(etype, hidden_ev["target_label"], person_id, pools,
                             correct_target, used_texts, config))
    if not _add(_pick_same_person(person_events, observed, missing_year, correct_target,
                                  used_texts, config, rng)):
        _add(_pick_near_year(etype, missing_year, person_id, pools, correct_target,
                             used_texts, config, rng, "same_type_near_year"))
    _add(_pick_random(etype, person_id, pools, correct_target, used_texts, config, rng, missing_year))
    while len(negatives) < 5:  # scarcity fallback, truthfully labelled
        if not _add(_pick_random(etype, person_id, pools, correct_target, used_texts, config, rng, missing_year)):
            break
    if len(negatives) < 5:
        return None

    cands = [correct] + negatives[:5]
    order = rng.permutation(len(cands))
    shuffled = [cands[int(i)] for i in order]
    for letter, cand in zip(LETTERS, shuffled):
        cand["candidate_id"] = letter
    correct_id = next(c["candidate_id"] for c in shuffled if c["distractor_type"] == "correct")
    return {
        "question_id": f"{person_id}_{missing_year}_{hidden_ev['property_id']}",
        "person_id": person_id,
        "person_label": hidden_ev["person_label"],
        "observed_events": observed,
        "missing_year": missing_year,
        "candidates": [{k: c.get(k) for k in ("candidate_id", "event_type", "target_id",
                                              "target_label", "text", "distractor_type")}
                       for c in shuffled],
        "correct_candidate_id": correct_id,
        "hidden_event_type": etype,
        "hidden_target_id": correct_target,
        "source": "wikidata",
        "split": split,
    }


def build_all_questions(grouped: dict[str, list[dict[str, Any]]], assignment: dict[str, str],
                        all_events: list[dict[str, Any]], config: dict[str, Any],
                        rng: np.random.Generator, targets: dict[str, int],
                        max_per_person: int) -> list[dict[str, Any]]:
    """Generate questions split by split until per-split targets are met (or persons run out).
    Pass 1 takes at most one question per person; pass 2 (if allowed) adds seconds."""
    pools = CandidatePools(all_events)
    questions: list[dict[str, Any]] = []
    for split in ("train", "calibration", "test"):
        split_persons = sorted(pid for pid, s in assignment.items() if s == split)
        order = rng.permutation(len(split_persons))
        split_persons = [split_persons[int(i)] for i in order]
        got: list[dict[str, Any]] = []
        used_years: dict[str, set[int]] = defaultdict(set)
        for round_no in range(max_per_person):
            for pid in split_persons:
                if len(got) >= targets[split]:
                    break
                years = [y for y in hideable_years(grouped[pid]) if y not in used_years[pid]]
                if len(used_years[pid]) > round_no:  # person already has enough questions
                    continue
                while years:
                    idx = int(rng.integers(len(years)))
                    y = years.pop(idx)
                    q = build_question(pid, grouped[pid], y, pools, config, rng, split)
                    if q is not None:
                        got.append(q)
                        used_years[pid].add(y)
                        break
            if len(got) >= targets[split]:
                break
        LOG.info("split %s: built %d questions (target %d) from %d persons",
                 split, len(got), targets[split], len(split_persons))
        questions.extend(got)
    return questions
