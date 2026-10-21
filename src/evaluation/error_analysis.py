"""Experiment 14: error analysis on the real out-of-fold spatial-CV
predictions from the PRIMARY model (no-RS Logistic Regression, n=209, 9
positive - EXP03b_10b), not the in-sample refit used for SHAP/mapping -
error analysis must use genuinely held-out predictions, not predictions
the model saw its own training label for.

Run directly: `python -m src.evaluation.error_analysis`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from models.train_baseline_models import FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, load_primary_dataset, RANDOM_SEED  # noqa: E402
from validation.spatial_blocks import assign_spatial_blocks, DEFAULT_BLOCK_SIZE_M  # noqa: E402

OUT_METRICS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"
OUT_TABLES = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "tables"


def get_oof_predictions(df: pd.DataFrame) -> np.ndarray:
    X = df[FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL].to_numpy()
    y = df["outcome"].to_numpy()
    groups = assign_spatial_blocks(df, DEFAULT_BLOCK_SIZE_M)
    n_splits = min(5, groups.nunique(), int(y.sum()))
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)

    oof = np.full(len(y), np.nan)
    for train_idx, test_idx in skf.split(X, y, groups=groups):
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X[train_idx])
        X_test = scaler.transform(X[test_idx])
        model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED)
        model.fit(X_train, y[train_idx])
        oof[test_idx] = model.predict_proba(X_test)[:, 1]
    return oof


def main() -> int:
    df = load_primary_dataset().reset_index(drop=True)
    oof_proba = get_oof_predictions(df)
    df["oof_proba"] = oof_proba
    df["oof_pred"] = (df["oof_proba"] >= 0.5).astype(int)

    valid = ~df["oof_proba"].isna()
    df_valid = df[valid]

    false_positives = df_valid[(df_valid["oof_pred"] == 1) & (df_valid["outcome"] == 0)]
    false_negatives = df_valid[(df_valid["oof_pred"] == 0) & (df_valid["outcome"] == 1)]
    true_positives = df_valid[(df_valid["oof_pred"] == 1) & (df_valid["outcome"] == 1)]
    true_negatives = df_valid[(df_valid["oof_pred"] == 0) & (df_valid["outcome"] == 0)]

    print(f"Out-of-fold confusion (threshold 0.5): TP={len(true_positives)}, FP={len(false_positives)}, "
          f"FN={len(false_negatives)}, TN={len(true_negatives)}")

    cols_to_show = [
        "event_id", "window", "outcome_name", "label_confidence_tier", "oof_proba",
        "area_m2", "agri_fraction_r100m", "years_since_conversion", "historical_ndvi_mean",
    ]

    print("\n--- False Positives (predicted recovery, actually persistent) ---")
    print(false_positives[cols_to_show].to_string(index=False) if len(false_positives) else "(none)")

    print("\n--- False Negatives (predicted persistent, actually recovery) ---")
    print(false_negatives[cols_to_show].to_string(index=False) if len(false_negatives) else "(none)")

    # Candidate explanations, checked against the ACTUAL data for these
    # specific misclassified parcels rather than asserted generically
    # (governing-brief Section AQ: "generate representative examples from
    # actual data, do not invent examples").
    findings = {
        "n_false_positives": len(false_positives),
        "n_false_negatives": len(false_negatives),
        "false_positive_events": false_positives[cols_to_show].to_dict(orient="records"),
        "false_negative_events": false_negatives[cols_to_show].to_dict(orient="records"),
    }

    if len(false_positives):
        fp_agri_frac = false_positives["agri_fraction_r100m"].mean()
        tn_agri_frac = true_negatives["agri_fraction_r100m"].mean()
        findings["false_positive_note"] = (
            f"Mean agri_fraction_r100m for false positives ({fp_agri_frac:.3f}) vs. true negatives "
            f"({tn_agri_frac:.3f}) - {'higher' if fp_agri_frac > tn_agri_frac else 'lower/similar'} "
            "surrounding-agriculture connectivity may explain why the model over-predicted recovery here."
        )
        print(f"\n{findings['false_positive_note']}")

    if len(false_negatives):
        fn_tier_counts = false_negatives["label_confidence_tier"].value_counts().to_dict()
        findings["false_negative_note"] = (
            f"False-negative label-confidence tier distribution: {fn_tier_counts} - if concentrated in "
            "Tier B (medium confidence), some of these 'errors' may reflect label uncertainty rather than "
            "genuine model failure."
        )
        print(f"\n{findings['false_negative_note']}")

    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_METRICS / "error_analysis.json").write_text(json.dumps(findings, indent=2, default=str))
    df_valid[cols_to_show + ["oof_pred"]].to_csv(OUT_TABLES / "table_oof_predictions.csv", index=False)
    print(f"\n[done] -> {OUT_METRICS / 'error_analysis.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
