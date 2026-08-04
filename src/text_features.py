"""Record rendering and TF-IDF features.

Leakage guards (adopted E-2 + spec):
- person_label is NEVER rendered into model input text;
- the vectorizer must be fitted on TRAIN records only (enforced by fit_vectorizer being
  the only fitting path, called with train texts by train_baseline).
"""

from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer


def render_record(question: dict[str, Any], candidate_text: str) -> str:
    """Render one (question, candidate) pair into the fixed 4-section text block."""
    before = [o["text"] for o in question["observed_events"] if o["year"] < question["missing_year"]]
    after = [o["text"] for o in question["observed_events"] if o["year"] > question["missing_year"]]
    lines = ["[CONTEXT]", *before,
             "[MISSING_YEAR]", str(question["missing_year"]),
             "[FUTURE_CONTEXT]", *after,
             "[CANDIDATE]", candidate_text]
    return "\n".join(lines)


def question_records(question: dict[str, Any]) -> list[tuple[str, str, str, int]]:
    """(question_id, candidate_id, rendered_text, label) for all 6 candidates."""
    out = []
    for cand in question["candidates"]:
        label = 1 if cand["candidate_id"] == question["correct_candidate_id"] else 0
        out.append((question["question_id"], cand["candidate_id"],
                    render_record(question, cand["text"]), label))
    return out


def make_vectorizer(config: dict[str, Any]) -> TfidfVectorizer:
    t = config["model"]["tfidf"]
    return TfidfVectorizer(ngram_range=(int(t["ngram_min"]), int(t["ngram_max"])),
                           min_df=int(t["min_df"]), max_features=int(t["max_features"]),
                           sublinear_tf=bool(t["sublinear_tf"]))


def fit_vectorizer(config: dict[str, Any], train_texts: list[str]) -> TfidfVectorizer:
    """Fit TF-IDF on TRAIN texts only (E-2). Never pass calibration/test texts here."""
    vec = make_vectorizer(config)
    vec.fit(train_texts)
    return vec
