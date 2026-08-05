"""End-to-end pipeline runner.

Usage:
    .venv/bin/python -m src.pipeline --profile dry --stage all
Stages: fetch, normalize, split, questions, train, conformal, evaluate, all.
Every stage writes its artifact to disk; later stages read from disk, so stages can be
re-run independently. A run manifest with the gate evidence is written per profile.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .conformal import attach_sets, calibration_scores, fit_all_qhats
from .evaluate import evaluate, write_example_cases
from .event_normalizer import normalize_events
from .question_builder import build_all_questions
from .split_people import eligible_persons, events_by_person, split_persons
from .train_baseline import predict_questions, train_model
from .utils import (PROJECT_ROOT, enabled_event_types, get_rng, load_config, profile_of,
                    read_json, read_jsonl, setup_logging, write_json, write_jsonl)
from .wikidata_client import WikidataClient

LOG = setup_logging()


def _paths(config: dict[str, Any], profile: str) -> dict[str, Path]:
    """Canonical spec paths belong to the full profile; other profiles get suffixed
    directories so a dry smoke run can never clobber the real dataset (A6 finding #3)."""
    p = config["paths"]
    sfx = "" if profile == "full" else f"-{profile}"
    processed = PROJECT_ROOT / (p["processed_dir"] + sfx)
    outputs = PROJECT_ROOT / (p["outputs_dir"] + sfx)
    return {"raw_persons": PROJECT_ROOT / p["raw_dir"] / f"phase1_person_counts_{profile}.json",
            "raw_events": PROJECT_ROOT / p["raw_dir"] / f"phase2_raw_events_{profile}.json",
            "events": processed / "person_events.jsonl",
            "person_split": processed / "person_split.json",
            "questions": processed / "life_event_questions.json",
            "splits_dir": PROJECT_ROOT / (p["splits_dir"] + sfx),
            "outputs": outputs,
            "predictions": outputs / "predictions.jsonl",
            "manifest": outputs / f"run_manifest_{profile}.json"}


def stage_fetch(config: dict[str, Any], profile: str) -> None:
    prof = profile_of(config, profile)
    paths = _paths(config, profile)
    client = WikidataClient(config)
    etypes = enabled_event_types(config)
    counts = client.discover_persons(etypes, int(prof["discovery_year_min"]), int(prof["discovery_year_max"]))
    write_json(paths["raw_persons"], counts)
    # Balanced pool: per event type take the densest K persons, union them — otherwise
    # award/position-heavy people crowd out education/employment questions entirely.
    per_type = max(1, int(prof["max_phase2_persons"]) // max(len(etypes), 1))
    pool: set[str] = set()
    for etype in sorted(etypes):
        ranked = sorted(((c.get(etype, 0), qid) for qid, c in counts.items() if c.get(etype, 0)),
                        key=lambda t: (-t[0], t[1]))
        pool.update(qid for _, qid in ranked[:per_type])
    pool_list = sorted(pool)
    LOG.info("phase1: %d persons discovered; balanced pool %d (top %d per type)",
             len(counts), len(pool_list), per_type)
    raw = client.fetch_person_events(pool_list, etypes)
    write_json(paths["raw_events"], raw)
    all_targets = client.fetch_all_targets(pool_list, etypes)
    write_json(paths["raw_events"].with_name(f"phase2_all_targets_{profile}.json"), all_targets)
    LOG.info("phase2: %d raw rows; all-targets for %d persons; %d network calls total",
             len(raw), len(all_targets), client.n_network_calls)


def stage_normalize(config: dict[str, Any], profile: str) -> None:
    paths = _paths(config, profile)
    raw = read_json(paths["raw_events"])
    events = normalize_events(raw, config)
    n = write_jsonl(paths["events"], events)
    LOG.info("normalize: wrote %d events -> %s", n, paths["events"])


def stage_split(config: dict[str, Any], profile: str) -> None:
    paths = _paths(config, profile)
    events = list(read_jsonl(paths["events"]))
    grouped = events_by_person(events)
    eligible = eligible_persons(grouped, config)
    rng = get_rng(config)
    assignment = split_persons(eligible, config, rng)
    write_json(paths["person_split"], assignment)


def stage_questions(config: dict[str, Any], profile: str) -> None:
    prof = profile_of(config, profile)
    paths = _paths(config, profile)
    events = list(read_jsonl(paths["events"]))
    grouped = events_by_person(events)
    assignment = read_json(paths["person_split"])
    at_path = paths["raw_events"].with_name(f"phase2_all_targets_{profile}.json")
    extra_targets = read_json(at_path) if at_path.exists() else None
    rng = get_rng(config)  # fresh seeded stream; question stage is self-contained
    questions = build_all_questions(grouped, assignment, events, config, rng,
                                    {k: int(v) for k, v in prof["question_targets"].items()},
                                    int(prof["max_questions_per_person"]), extra_targets)
    write_json(paths["questions"], questions)
    for split in ("train", "calibration", "test"):
        write_jsonl(paths["splits_dir"] / f"{split}.jsonl", [q for q in questions if q["split"] == split])
    LOG.info("questions: %s", Counter(q["split"] for q in questions))


def _load_split_questions(paths: dict[str, Path], split: str) -> list[dict[str, Any]]:
    return list(read_jsonl(paths["splits_dir"] / f"{split}.jsonl"))


def stage_train(config: dict[str, Any], profile: str) -> None:
    paths = _paths(config, profile)
    train_qs = _load_split_questions(paths, "train")
    vec, clf = train_model(config, train_qs)
    preds = []
    for split in ("train", "calibration", "test"):
        preds.extend(predict_questions(vec, clf, _load_split_questions(paths, split)))
    write_jsonl(paths["predictions"], preds)
    n_ok = sum(1 for p in preds if p["split"] == "train" and p["point_prediction"] == p["correct_candidate_id"])
    n_tr = sum(1 for p in preds if p["split"] == "train")
    LOG.info("train accuracy (sanity, in-sample): %.3f", n_ok / max(n_tr, 1))


def stage_conformal(config: dict[str, Any], profile: str) -> None:
    paths = _paths(config, profile)
    preds = list(read_jsonl(paths["predictions"]))
    cal = [p for p in preds if p["split"] == "calibration"]
    scores = calibration_scores(cal)
    q_hats = fit_all_qhats(scores, [float(a) for a in config["alphas"]])
    write_json(paths["outputs"] / "qhats.json", {"n_calibration": len(cal), "q_hats": q_hats})
    write_jsonl(paths["predictions"], attach_sets(preds, q_hats))
    LOG.info("conformal: n_cal=%d q_hats=%s", len(cal), q_hats)


def stage_evaluate(config: dict[str, Any], profile: str) -> None:
    paths = _paths(config, profile)
    preds = [p for p in read_jsonl(paths["predictions"]) if p["split"] == "test"]
    test_qs = _load_split_questions(paths, "test")
    summary = evaluate(test_qs, preds, paths["outputs"])
    write_example_cases(test_qs, preds, paths["outputs"])

    # Gate evidence for the scale-up decision (老板扩容闸门).
    questions = read_json(paths["questions"])
    assignment = read_json(paths["person_split"])
    persons_per_split: dict[str, set] = {"train": set(), "calibration": set(), "test": set()}
    for q in questions:
        persons_per_split[q["split"]].add(q["person_id"])
    manifest = {
        "profile": profile,
        "questions_per_split": dict(Counter(q["split"] for q in questions)),
        "eligible_persons": len(assignment),
        "distractor_type_counts": dict(Counter(c["distractor_type"] for q in questions
                                               for c in q["candidates"])),
        "person_split_disjoint": not (persons_per_split["train"] & persons_per_split["calibration"]
                                      or persons_per_split["train"] & persons_per_split["test"]
                                      or persons_per_split["calibration"] & persons_per_split["test"]),
        "summary": summary,
    }
    write_json(paths["manifest"], manifest)
    LOG.info("manifest -> %s", paths["manifest"])


STAGES = {"fetch": stage_fetch, "normalize": stage_normalize, "split": stage_split,
          "questions": stage_questions, "train": stage_train, "conformal": stage_conformal,
          "evaluate": stage_evaluate}


def main() -> None:
    ap = argparse.ArgumentParser(description="LifeEvent-CP pipeline")
    ap.add_argument("--profile", choices=["dry", "full"], required=True)
    ap.add_argument("--stage", choices=[*STAGES, "all"], default="all")
    args = ap.parse_args()
    config = load_config()
    stages = list(STAGES) if args.stage == "all" else [args.stage]
    for name in stages:
        LOG.info("=== stage %s (%s) ===", name, args.profile)
        STAGES[name](config, args.profile)


if __name__ == "__main__":
    main()
