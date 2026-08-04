"""TF-IDF + Logistic Regression baseline with per-question softmax scores.

The classifier is binary per (question, candidate) record; A–F are NOT global classes.
Within each question the six decision-function logits are softmaxed into scores.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from .text_features import fit_vectorizer, question_records
from .utils import setup_logging

LOG = setup_logging()


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def train_model(config: dict[str, Any], train_questions: list[dict[str, Any]]):
    """Fit vectorizer (train only, E-2) and logistic regression on train records."""
    records = [r for q in train_questions for r in question_records(q)]
    texts = [r[2] for r in records]
    labels = np.array([r[3] for r in records])
    vec = fit_vectorizer(config, texts)
    x = vec.transform(texts)
    lr_cfg = config["model"]["logreg"]
    clf = LogisticRegression(class_weight=lr_cfg["class_weight"], max_iter=int(lr_cfg["max_iter"]),
                             random_state=int(lr_cfg["random_state"]))
    clf.fit(x, labels)
    LOG.info("trained on %d records (%d questions), vocab %d",
             x.shape[0], len(train_questions), len(vec.vocabulary_))
    return vec, clf


def predict_questions(vec, clf, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-question candidate scores (softmax over the 6 logits) + point prediction."""
    preds = []
    for q in questions:
        recs = question_records(q)
        logits = clf.decision_function(vec.transform([r[2] for r in recs]))
        probs = _softmax(np.asarray(logits, dtype=float))
        cand_ids = [r[1] for r in recs]
        scores = {cid: float(p) for cid, p in zip(cand_ids, probs)}
        point = max(scores, key=lambda c: (scores[c], c))
        preds.append({"question_id": q["question_id"], "split": q["split"],
                      "candidate_scores": scores, "point_prediction": point,
                      "correct_candidate_id": q["correct_candidate_id"]})
    return preds
