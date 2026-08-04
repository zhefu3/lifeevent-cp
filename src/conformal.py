"""Split conformal prediction, LAC score (v0).

score s_i = 1 - p_i(y_i) on calibration; finite-sample quantile level
q_level = min(1, ceil((n+1)*(1-alpha)) / n) taken with np.quantile(..., method="higher").
This is the standard tutorial recipe (Angelopoulos & Bates); it is conservative by at
most one order statistic relative to the k-th-smallest formulation, so the >= 1-alpha
marginal coverage guarantee is preserved.

Prediction set C(x) = {j : 1 - p_j(x) <= q_hat}. Empty sets are allowed and reported;
the argmax is never force-inserted.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def calibration_scores(cal_predictions: list[dict[str, Any]]) -> np.ndarray:
    """LAC nonconformity scores from CALIBRATION predictions only."""
    return np.array([1.0 - p["candidate_scores"][p["correct_candidate_id"]]
                     for p in cal_predictions], dtype=float)


def quantile_level(n: int, alpha: float) -> float:
    return min(1.0, math.ceil((n + 1) * (1.0 - alpha)) / n)


def fit_qhat(scores: np.ndarray, alpha: float) -> float:
    """Finite-sample adjusted empirical quantile of calibration scores."""
    if len(scores) == 0:
        raise ValueError("empty calibration scores")
    return float(np.quantile(scores, quantile_level(len(scores), alpha), method="higher"))


def fit_all_qhats(scores: np.ndarray, alphas: list[float]) -> dict[str, float]:
    """alpha -> q_hat, keyed by coverage string ('0.80' for alpha 0.20)."""
    return {f"{1.0 - a:.2f}": fit_qhat(scores, a) for a in alphas}


def prediction_set(candidate_scores: dict[str, float], q_hat: float) -> list[str]:
    """Candidates whose nonconformity 1-p is within the threshold (may be empty)."""
    return sorted([c for c, p in candidate_scores.items() if 1.0 - p <= q_hat])


def attach_sets(predictions: list[dict[str, Any]], q_hats: dict[str, float]) -> list[dict[str, Any]]:
    """Add conformal_sets to each prediction row (non-destructive copy)."""
    out = []
    for p in predictions:
        sets = {cov: prediction_set(p["candidate_scores"], q) for cov, q in sorted(q_hats.items())}
        out.append({**p, "conformal_sets": sets})
    return out
