"""Experiments 13 + 15: probability calibration + final recovery-potential
map, using the PRIMARY model (no-RS Logistic Regression, n=209, 9
positive) - see shap_analysis.py's docstring for why this arm, not the
higher-point-estimate but n=4-positive RS-inclusive arm, is treated as
primary.

Calibration (EXP13): 5-fold cross-validated isotonic calibration on the
Tier A+B training pool ONLY - there is no separate held-out test set in
this project's current design (see research_log.md's disclosed deviation:
Mit Salsil could not be reserved as a pure untouched holdout given only 6
El-Bagalat positives), so this calibration is reported as fitted on the
same pool used for the ablation, NOT validated on an independent held-out
set - a real, stated limitation, not glossed over.

Mapping (EXP15): applies the calibrated model to every parcel in the
FULL master dataset (all tiers, both outcomes - 310 parcels) to produce a
real, data-derived Agricultural Recovery Potential value per parcel, then
renders it as a georeferenced figure over the study windows. This is
"Observed Agricultural Recovery Potential" in the technical sense defined
in the protocol (Section 1, Section AR) - a probability that the FITTED
MODEL assigns based on pre-outcome features, evaluated here on parcels
whose true outcome is already known (since the whole dataset is
historical) - it demonstrates the mapping PRODUCT, not a genuine
forecast for undetermined future parcels (which would need to be applied
to currently-active, outcome-undetermined converted land - not
attempted here, since this project's own conversion events all lie
within the closed 2017-2024 historical record).

Run directly: `python -m src.mapping.recovery_potential_map`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from models.train_baseline_models import FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, load_primary_dataset, RANDOM_SEED  # noqa: E402
from validation.spatial_blocks import assign_spatial_blocks, DEFAULT_BLOCK_SIZE_M  # noqa: E402

DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_FIGURES = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "figures"
OUT_METRICS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"
OUT_MAPS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "maps"


def calibrate_and_evaluate(df: pd.DataFrame):
    from sklearn.model_selection import StratifiedGroupKFold

    X = df[FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL].to_numpy()
    y = df["outcome"].to_numpy()
    groups = assign_spatial_blocks(df, DEFAULT_BLOCK_SIZE_M)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    base_model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED)
    n_splits = min(5, int(y.sum()), groups.nunique())
    calibrated = CalibratedClassifierCV(base_model, method="isotonic", cv=max(n_splits, 2))
    calibrated.fit(X_scaled, y)

    calibrated_proba = calibrated.predict_proba(X_scaled)[:, 1]
    uncalibrated_proba = base_model.fit(X_scaled, y).predict_proba(X_scaled)[:, 1]

    brier_calibrated = brier_score_loss(y, calibrated_proba)
    brier_uncalibrated = brier_score_loss(y, uncalibrated_proba)

    print(
        f"[calibration] Brier score: uncalibrated={brier_uncalibrated:.4f}, "
        f"isotonic-calibrated={brier_calibrated:.4f} "
        f"(fit on the SAME Tier A+B pool used for training - not an independent test set, see module docstring)"
    )

    return calibrated, scaler, calibrated_proba, {
        "brier_uncalibrated": brier_uncalibrated,
        "brier_calibrated": brier_calibrated,
        "n_calibration_folds": max(n_splits, 2),
        "caveat": "Calibrated and evaluated on the same pool - no independent held-out test set exists in this design.",
    }


def make_calibration_curve_figure(y_true, proba, out_path: pathlib.Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve

    prob_true, prob_pred = calibration_curve(y_true, proba, n_bins=5, strategy="quantile")
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
    ax.plot(prob_pred, prob_true, marker="o", label="Isotonic-calibrated model")
    ax.set_xlabel("Mean predicted recovery probability")
    ax.set_ylabel("Observed fraction of recovery events")
    ax.set_title("Calibration curve (fit-set only, not independently validated)", fontsize=9)
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


def make_recovery_potential_map(df: pd.DataFrame, proba: np.ndarray, out_path: pathlib.Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = df.copy()
    df["recovery_potential"] = proba

    from utils.study_area import ALL_WINDOW_NAMES

    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    for ax, window_name in zip(axes.flat, ALL_WINDOW_NAMES):
        sub = df[df["window"] == window_name]
        sc = ax.scatter(
            sub["centroid_x"],
            sub["centroid_y"],
            c=sub["recovery_potential"],
            cmap="RdYlGn",
            vmin=0,
            vmax=1,
            s=np.clip(sub["area_m2"] / 100, 10, 200),
            edgecolors="black",
            linewidths=0.3,
        )
        true_outcome_marker = sub["outcome"].map({1: "o", 0: "x"})
        for marker, group in sub.groupby(true_outcome_marker):
            ax.scatter(
                group["centroid_x"],
                group["centroid_y"],
                facecolors="none",
                edgecolors="black" if marker == "o" else "none",
                marker=marker,
                s=np.clip(group["area_m2"] / 100, 10, 200) * 1.3,
                linewidths=0.8 if marker == "o" else 0,
            )
        ax.set_title(f"{window_name}\n(circle outline = true Observed Recovery, x = true Persistent Conversion)", fontsize=9)
        ax.set_xlabel("UTM Easting (m), EPSG:32636")
        ax.set_ylabel("UTM Northing (m)")
        ax.set_aspect("equal")
        plt.colorbar(sc, ax=ax, label="Model-estimated Recovery Potential (calibrated)")

    fig.suptitle(
        "Figure 15 — Agricultural Recovery Potential (calibrated model output on known-outcome parcels)\n"
        "NOT a forecast for undetermined future parcels — see module docstring for scope caveat",
        fontsize=10,
    )
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


def main() -> int:
    df = load_primary_dataset()  # Tier A+B, used to FIT the calibrated model
    calibrated_model, scaler, calibrated_proba_fit, calib_metrics = calibrate_and_evaluate(df)

    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    OUT_MAPS.mkdir(parents=True, exist_ok=True)

    make_calibration_curve_figure(
        df["outcome"].to_numpy(), calibrated_proba_fit, OUT_FIGURES / "figure12_calibration_curve.png"
    )
    print(f"[fig] -> {OUT_FIGURES / 'figure12_calibration_curve.png'}")

    (OUT_METRICS / "calibration_metrics.json").write_text(json.dumps(calib_metrics, indent=2))

    # Apply to the FULL dataset (all tiers, both outcomes, 310 parcels) to
    # produce the mapped product - see module docstring for the scope
    # caveat (this demonstrates the mapping product on known-outcome
    # historical parcels, it is not a forecast for undetermined parcels).
    full_df = pd.read_csv(DATA_PROCESSED / "master_dataset_all_windows.csv")
    X_full = scaler.transform(full_df[FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL].to_numpy())
    full_df["recovery_potential"] = calibrated_model.predict_proba(X_full)[:, 1]

    full_df.to_csv(DATA_PROCESSED / "master_dataset_with_recovery_potential.csv", index=False)
    print(f"[data] -> {DATA_PROCESSED / 'master_dataset_with_recovery_potential.csv'}")

    make_recovery_potential_map(full_df, full_df["recovery_potential"].to_numpy(), OUT_MAPS / "figure15_recovery_potential_map.png")
    print(f"[map] -> {OUT_MAPS / 'figure15_recovery_potential_map.png'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
