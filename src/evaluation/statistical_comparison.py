"""Experiment 11: formal statistical comparison between models/feature-sets
(governing-brief Section 18 / AM). Implements:
  - Paired bootstrap confidence interval on a metric DIFFERENCE (not just
    each model's own CI separately - the difference's own CI is what
    actually tests whether one model beats another).
  - McNemar's test on paired binary predictions (correct/incorrect) at a
    fixed threshold.
  - A DeLong-style paired test for ROC-AUC difference (via a bootstrap
    approximation, documented as such - the exact analytic DeLong
    covariance formula is not implemented here; the paired bootstrap is a
    standard, valid substitute and is reported as such, not mislabeled as
    the analytic DeLong test).

Run directly: `python -m src.evaluation.statistical_comparison`
(expects out-of-fold prediction arrays for two models to be compared,
passed in by the caller - see __main__ for the expected input format)
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from statsmodels.stats.contingency_tables import mcnemar


def paired_bootstrap_diff_ci(y_true, proba_a, proba_b, metric_fn, n_boot=2000, seed=42, alpha=0.05):
    """95% CI on metric_fn(model_a) - metric_fn(model_b), resampling
    (y_true, proba_a, proba_b) jointly so the pairing between the two
    models' predictions on the SAME instances is preserved."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    y_true, proba_a, proba_b = np.asarray(y_true), np.asarray(proba_a), np.asarray(proba_b)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt = y_true[idx]
        if len(np.unique(yt)) < 2:
            continue
        try:
            diffs.append(metric_fn(yt, proba_a[idx]) - metric_fn(yt, proba_b[idx]))
        except ValueError:
            continue
    if not diffs:
        return {"point_diff": np.nan, "ci_low": np.nan, "ci_high": np.nan, "n_valid_boot": 0}
    diffs = np.array(diffs)
    point = metric_fn(y_true, proba_a) - metric_fn(y_true, proba_b)
    return {
        "point_diff": float(point),
        "ci_low": float(np.percentile(diffs, 100 * alpha / 2)),
        "ci_high": float(np.percentile(diffs, 100 * (1 - alpha / 2))),
        "ci_excludes_zero": bool(np.percentile(diffs, 100 * alpha / 2) > 0 or np.percentile(diffs, 100 * (1 - alpha / 2)) < 0),
        "n_valid_boot": int(len(diffs)),
    }


def mcnemar_test(y_true, pred_a, pred_b):
    """McNemar's test on paired binary predictions: compares the two
    models' DISCORDANT predictions only (cases where they disagree)."""
    y_true, pred_a, pred_b = np.asarray(y_true), np.asarray(pred_a), np.asarray(pred_b)
    a_correct = pred_a == y_true
    b_correct = pred_b == y_true
    n01 = int(np.sum(a_correct & ~b_correct))  # a right, b wrong
    n10 = int(np.sum(~a_correct & b_correct))  # a wrong, b right
    table = [[0, n01], [n10, 0]]
    result = mcnemar(table, exact=(n01 + n10) < 25)
    return {"n01": n01, "n10": n10, "statistic": float(result.statistic), "p_value": float(result.pvalue)}


def compare_two_models(y_true, proba_a, proba_b, name_a: str, name_b: str, threshold: float = 0.5):
    result = {
        "model_a": name_a,
        "model_b": name_b,
        "pr_auc_diff": paired_bootstrap_diff_ci(y_true, proba_a, proba_b, average_precision_score),
        "roc_auc_diff_bootstrap": paired_bootstrap_diff_ci(y_true, proba_a, proba_b, roc_auc_score),
        "mcnemar_at_threshold": mcnemar_test(
            y_true, (np.asarray(proba_a) >= threshold).astype(int), (np.asarray(proba_b) >= threshold).astype(int)
        ),
    }
    return result


if __name__ == "__main__":
    print(
        "This module provides comparison functions; it is invoked from "
        "src/models/train_baseline_models.py (or a dedicated re-run script) "
        "once out-of-fold predictions for two models on the SAME dataset "
        "exist. It is not a standalone script with its own data source."
    )
