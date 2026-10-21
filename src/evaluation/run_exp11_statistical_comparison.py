"""Experiment 11: formal statistical comparison between the top two models
on the primary (no-RS, n=209, 9 positive) ablation arm, using the
functions in statistical_comparison.py. Compares Random Forest (highest
point-estimate PR-AUC in EXP03b_10b) against Logistic Regression (the
project's primary reported model, chosen for interpretability/stability,
not because it scored highest).

Run directly: `python -m src.evaluation.run_exp11_statistical_comparison`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from evaluation.statistical_comparison import compare_two_models  # noqa: E402
from models.train_baseline_models import FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, RANDOM_SEED, load_primary_dataset  # noqa: E402
from validation.spatial_blocks import DEFAULT_BLOCK_SIZE_M, assign_spatial_blocks  # noqa: E402

OUT_METRICS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"


def main() -> int:
    df = load_primary_dataset().reset_index(drop=True)
    X = df[FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL].to_numpy()
    y = df["outcome"].to_numpy()
    groups = assign_spatial_blocks(df, DEFAULT_BLOCK_SIZE_M)
    n_splits = min(5, groups.nunique(), int(y.sum()))
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)

    oof_lr = np.full(len(y), np.nan)
    oof_rf = np.full(len(y), np.nan)
    for train_idx, test_idx in skf.split(X, y, groups=groups):
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X[train_idx])
        X_test = scaler.transform(X[test_idx])

        lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED)
        lr.fit(X_train, y[train_idx])
        oof_lr[test_idx] = lr.predict_proba(X_test)[:, 1]

        rf = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=RANDOM_SEED, max_depth=5)
        rf.fit(X_train, y[train_idx])
        oof_rf[test_idx] = rf.predict_proba(X_test)[:, 1]

    valid = ~np.isnan(oof_lr) & ~np.isnan(oof_rf)
    result = compare_two_models(y[valid], oof_rf[valid], oof_lr[valid], "random_forest", "logistic_regression")
    print(json.dumps(result, indent=2, default=str))

    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    out_path = OUT_METRICS / "statistical_comparison_rf_vs_logreg.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"[done] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
