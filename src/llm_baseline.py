"""v1: LLM six-way scoring baseline over the SAME questions and conformal harness.

Channel: the boss's Claude membership CLI (`claude -p`), never the paid API — the
subprocess env explicitly drops ANTHROPIC_API_KEY. Batch armour (house lesson 0023):
hard timeout + 1 retry + skip-on-fail, and every response is cached on disk so reruns
never re-invoke the CLI.

Methodology guards:
- prompt development is allowed on TRAIN questions only (--split train_dev);
- calibration/test are scored with the frozen prompt; test is never used to tune;
- model input contains no person names (same renderer sections as text_features);
- parse failures fall back to uniform 1/6 and are counted + reported, not hidden.

Contamination probe (--probe): the questions concern public figures, so an LLM may
recognise the person from the nameless timeline and answer from memorised knowledge
rather than timeline reasoning. We quantify that risk: ask the model to NAME the person
for a sample of test questions and report the hit rate alongside the accuracy numbers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .utils import PROJECT_ROOT, read_jsonl, setup_logging, sha1_of, write_json, write_jsonl

LOG = setup_logging()

LETTERS = ["A", "B", "C", "D", "E", "F"]

SCORE_PROMPT = """You are given a partial, year-stamped timeline of an anonymous public figure. One event from a middle year has been hidden. Exactly one of the six candidates below is the hidden event recorded for that year.

[CONTEXT]
{before}
[MISSING_YEAR]
{year}
[FUTURE_CONTEXT]
{after}
[CANDIDATES]
{candidates}

Assign each candidate a probability that it is the hidden event for year {year}. Probabilities must be positive and sum to 1. Respond with ONLY a JSON object, no other text, e.g. {{"A":0.4,"B":0.2,"C":0.15,"D":0.1,"E":0.1,"F":0.05}}"""

PROBE_PROMPT = """Below is a partial, year-stamped timeline of a real public figure whose name has been removed. If you can identify who this person is, give their name; otherwise use null.

{timeline}

Respond with ONLY a JSON object: {{"name": "Full Name or null", "confidence": 0.0}}"""


def _cli_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)  # membership quota, $0 — never the paid API
    return env


def _cache_path(kind: str, key: str) -> Path:
    d = PROJECT_ROOT / "data" / "raw" / "llm"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{kind}_{key}.json"


def call_claude(prompt: str, model: str, timeout_s: int, cache_kind: str, cache_key: str) -> str | None:
    """One membership-CLI call with cache + 1 retry + skip-on-fail. Returns raw text."""
    cpath = _cache_path(cache_kind, cache_key)
    if cpath.exists():
        return json.loads(cpath.read_text(encoding="utf-8"))["raw"]
    for attempt in range(2):
        try:
            proc = subprocess.run(
                ["claude", "-p", prompt, "--model", model],
                env=_cli_env(), capture_output=True, text=True, timeout=timeout_s)
            if proc.returncode == 0 and proc.stdout.strip():
                raw = proc.stdout.strip()
                cpath.write_text(json.dumps({"prompt_sha1": sha1_of(prompt), "raw": raw},
                                            ensure_ascii=False), encoding="utf-8")
                return raw
            LOG.warning("claude CLI rc=%d attempt %d: %s", proc.returncode, attempt + 1,
                        proc.stderr.strip()[:200])
        except subprocess.TimeoutExpired:
            LOG.warning("claude CLI timeout (%ds) attempt %d", timeout_s, attempt + 1)
    return None  # skip-on-fail; caller records the failure


def _extract_json(raw: str) -> dict[str, Any] | None:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def render_score_prompt(question: dict[str, Any]) -> str:
    before = "\n".join(o["text"] for o in question["observed_events"]
                       if o["year"] < question["missing_year"]) or "(none)"
    after = "\n".join(o["text"] for o in question["observed_events"]
                      if o["year"] > question["missing_year"]) or "(none)"
    cands = "\n".join(f"{c['candidate_id']}: {c['text']}" for c in question["candidates"])
    return SCORE_PROMPT.format(before=before, year=question["missing_year"], after=after, candidates=cands)


def score_question(question: dict[str, Any], model: str, timeout_s: int) -> dict[str, Any]:
    """Score one question; uniform fallback (flagged) when the call or parse fails."""
    prompt = render_score_prompt(question)
    raw = call_claude(prompt, model, timeout_s, "score", f"{question['question_id']}_{sha1_of(prompt)[:12]}")
    scores, ok = None, False
    if raw is not None:
        obj = _extract_json(raw)
        if obj:
            try:
                vals = {c: max(float(obj.get(c, 0.0)), 0.0) for c in LETTERS}
                total = sum(vals.values())
                if total > 0:
                    scores = {c: v / total for c, v in vals.items()}
                    ok = True
            except (TypeError, ValueError):
                pass
    if scores is None:
        scores = {c: 1.0 / 6.0 for c in LETTERS}
    point = max(scores, key=lambda c: (scores[c], c))
    return {"question_id": question["question_id"], "split": question["split"],
            "candidate_scores": scores, "point_prediction": point,
            "correct_candidate_id": question["correct_candidate_id"], "parse_ok": ok}


def run_scoring(questions: list[dict[str, Any]], model: str, timeout_s: int, workers: int) -> list[dict[str, Any]]:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        preds = list(ex.map(lambda q: score_question(q, model, timeout_s), questions))
    n_fail = sum(1 for p in preds if not p["parse_ok"])
    LOG.info("LLM scored %d questions (%d parse/call failures -> uniform fallback)", len(preds), n_fail)
    return preds


def probe_question(question: dict[str, Any], model: str, timeout_s: int) -> dict[str, Any]:
    timeline = "\n".join(o["text"] for o in question["observed_events"])
    prompt = PROBE_PROMPT.format(timeline=timeline)
    raw = call_claude(prompt, model, timeout_s, "probe", f"{question['question_id']}_{sha1_of(prompt)[:12]}")
    guess, conf = None, None
    if raw is not None:
        obj = _extract_json(raw)
        if obj:
            guess = obj.get("name")
            conf = obj.get("confidence")
    truth = question["person_label"]
    def _norm(s: str) -> str:
        return re.sub(r"[^a-z ]", "", s.lower()).strip()
    hit = bool(guess) and isinstance(guess, str) and guess.lower() != "null" and (
        _norm(guess) == _norm(truth) or _norm(guess) in _norm(truth) or _norm(truth) in _norm(guess))
    return {"question_id": question["question_id"], "person_label": truth,
            "guess": guess, "confidence": conf, "hit": hit}


def main() -> None:
    ap = argparse.ArgumentParser(description="LLM baseline over membership CLI")
    ap.add_argument("--split", choices=["train_dev", "calibration", "test", "eval"], default="eval",
                    help="train_dev: prompt development sample; eval = calibration + test; ignored with --probe")
    ap.add_argument("--n", type=int, default=20, help="sample size for train_dev / probe")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--probe", action="store_true", help="run contamination probe on test sample")
    args = ap.parse_args()

    splits_dir = PROJECT_ROOT / "data" / "splits"
    outdir = PROJECT_ROOT / "outputs" / "llm"
    outdir.mkdir(parents=True, exist_ok=True)

    if args.probe:
        test_qs = list(read_jsonl(splits_dir / "test.jsonl"))[: args.n]
        rows = [probe_question(q, args.model, args.timeout) for q in test_qs]
        rate = sum(r["hit"] for r in rows) / len(rows)
        write_json(outdir / "contamination_probe.json",
                   {"n": len(rows), "identified_rate": rate, "rows": rows})
        LOG.info("probe: %d/%d identified (%.2f)", sum(r["hit"] for r in rows), len(rows), rate)
        return

    if args.split == "train_dev":
        qs = list(read_jsonl(splits_dir / "train.jsonl"))[: args.n]
        preds = run_scoring(qs, args.model, args.timeout, args.workers)
        acc = sum(p["point_prediction"] == p["correct_candidate_id"] for p in preds) / len(preds)
        write_jsonl(outdir / "train_dev_predictions.jsonl", preds)
        LOG.info("train_dev accuracy %.3f (n=%d) — prompt development only", acc, len(preds))
        return

    names = ["calibration", "test"] if args.split == "eval" else [args.split]
    preds: list[dict[str, Any]] = []
    for name in names:
        qs = list(read_jsonl(splits_dir / f"{name}.jsonl"))
        preds.extend(run_scoring(qs, args.model, args.timeout, args.workers))
    write_jsonl(outdir / "predictions_llm.jsonl", preds)
    LOG.info("wrote %d LLM predictions", len(preds))


if __name__ == "__main__":
    main()
