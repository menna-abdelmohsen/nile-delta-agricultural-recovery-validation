"""Experiment 12: SHAP explainability on the PRIMARY model - Logistic
Regression on the no-RS (GIS+Geometric+Environmental+Temporal) feature
set, chosen as primary because it is the only ablation arm with enough
positive cases (n=209 parcels, 9 positive) for a remotely stable estimate
(see research_log.md, 2026-09-21 continued 9, for why the RS-inclusive
arm's much higher point estimates at n=4 positives are NOT trustworthy).
Refit on the FULL Tier A+B dataset for the explanation model, since SHAP
here characterizes what the model learned overall, not out-of-sample
performance (already reported separately via spatial CV, EXP03b_10b).

Per governing-brief Section AN: SHAP values describe MODEL ASSOCIATIONS,
not causal effects - this caveat is written directly into every figure
caption and the printed summary, not left implicit.

Run directly: `python -m src.explainability.shap_analysis`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from models.train_baseline_models import FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, load_primary_dataset, RANDOM_SEED  # noqa: E402

OUT_FIGURES = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "figures"
OUT_METRICS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"


def main() -> int:
    df = load_primary_dataset()
    X_raw = df[FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL].to_numpy()
    y = df["outcome"].to_numpy()

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED)
    model.fit(X, y)

    explainer = shap.LinearExplainer(model, X)
    shap_values = explainer.shap_values(X)

    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance_order = np.argsort(mean_abs_shap)[::-1]

    print("SHAP mean |value| by feature (model association strength, NOT causal effect):")
    importance_table = []
    for idx in importance_order:
        feat = FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL[idx]
        val = float(mean_abs_shap[idx])
        coef_sign = "+" if model.coef_[0][idx] > 0 else "-"
        print(f"  {feat:30s} mean|SHAP|={val:.4f}  (logistic coef sign: {coef_sign})")
        importance_table.append({"feature": feat, "mean_abs_shap": val, "coef_sign": coef_sign})

    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    OUT_METRICS.mkdir(parents=True, exist_ok=True)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    shap.summary_plot(shap_values, X_raw, feature_names=FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, show=False)
    plt.title(
        "SHAP summary — associations with model output only, not causal effects\n"
        f"(Logistic Regression, no-RS primary model, Tier A+B parcels, n={len(df)}, {int(y.sum())} positive)",
        fontsize=9,
    )
    plt.tight_layout()
    fig_path = OUT_FIGURES / "figure13_shap_summary.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"[fig] -> {fig_path}")

    # Dependence plot for the single most important feature (Figure 14).
    top_feature_idx = importance_order[0]
    top_feature_name = FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL[top_feature_idx]
    fig, ax = plt.subplots(figsize=(7, 5))
    shap.dependence_plot(
        top_feature_idx, shap_values, X_raw, feature_names=FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, show=False, ax=ax
    )
    ax.set_title(f"SHAP dependence — {top_feature_name} (association only, not causal)", fontsize=9)
    plt.tight_layout()
    fig_path2 = OUT_FIGURES / "figure14_shap_dependence_top_feature.png"
    plt.savefig(fig_path2, dpi=300)
    plt.close()
    print(f"[fig] -> {fig_path2}")

    result = {
        "model": "logistic_regression_no_RS_primary_refit_on_full_tierAB",
        "n_parcels": len(df),
        "n_positive": int(y.sum()),
        "feature_importance_by_mean_abs_shap": importance_table,
        "caveat": (
            "SHAP values describe associations the fitted model relied on, "
            "not causal drivers of recovery. Refit on the full dataset for "
            "interpretability; out-of-sample performance is reported "
            "separately from spatial cross-validation (EXP03-10)."
        ),
    }
    out_path = OUT_METRICS / "shap_feature_importance.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"[done] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
