"""Experiments 3-7 (baseline models + spatial CV), run on the REAL Tier
A+B parcel dataset (157 parcels: 16 recovery, 141 persistent - pooled
across both windows, per the honest small-N adaptation logged in
research_log.md: El-Bagalat alone has only 6 positive parcels, too few
for spatial-block CV on its own, so the strict "train on El-Bagalat only,
never touch Mit Salsil" plan from protocol Section 3/9 was infeasible as
originally written and is REPLACED here by pooled spatial-block CV as the
primary evaluation, with a leave-one-region-out check as a secondary,
explicitly exploratory result - this deviation is disclosed, not hidden).

Feature set used here is deliberately RS-FEATURE-FREE for now: Sentinel-2
NDVI composites are still downloading for Mit Salsil at the time this was
first run (see research_log.md), so including NDVI features would silently
NaN-fill half the dataset. This is documented as Model set "B" (GIS +
Geometric + Environmental + Temporal, no Remote Sensing) in the governing
protocol's ablation framework (Section AP) - not a shortcut, but literally
one of the ablation arms the protocol already called for, run first
because its inputs happened to be ready first.

Run directly: `python -m src.models.train_baseline_models`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from validation.spatial_blocks import assign_spatial_blocks, DEFAULT_BLOCK_SIZE_M  # noqa: E402

DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_METRICS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"
OUT_MODELS = pathlib.Path(__file__).resolve().parents[2] / "models"

FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL = [
    "area_m2",
    "perimeter_m",
    "compactness",
    "conversion_year",
    "years_since_conversion",
    "mean_elevation_m",
    "elevation_range_m",
    "distance_to_agriculture_m",
    "agri_fraction_r100m",
    "agri_fraction_r250m",
    "agri_fraction_r500m",
    "distance_to_road_m",
    "distance_to_irrigation_m",
    "builtup_fraction_r100m",
    "builtup_fraction_r250m",
    "builtup_fraction_r500m",
]
FEATURE_COLS_RS_ONLY = [
    "historical_ndvi_mean",
    "historical_ndvi_max",
    "historical_ndvi_std",
]
FEATURE_COLS_ALL = FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL + FEATURE_COLS_RS_ONLY

# Backward-compatible alias used by earlier runs logged in research_log.md
# (EXP03-07, executed before Sentinel-2 NDVI was available) - kept so that
# re-running this exact script reproduces that logged result if invoked
# with this name specifically, rather than silently changing meaning.
FEATURE_COLS_NO_RS = FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL

RANDOM_SEED = 42
N_SPLITS = 5


def load_primary_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PROCESSED / "master_dataset_all_windows.csv")
    primary = df[df["label_confidence_tier"].isin(["A", "B"])].reset_index(drop=True)
    return primary


def bootstrap_ci(metric_fn, y_true, y_score, n_boot=2000, seed=RANDOM_SEED, alpha=0.05):
    rng = np.random.default_rng(seed)
    n = len(y_true)
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        y_t, y_s = np.asarray(y_true)[idx], np.asarray(y_score)[idx]
        if len(np.unique(y_t)) < 2:
            continue  # a bootstrap resample with only one class can't score AUC/AP
        try:
            stats.append(metric_fn(y_t, y_s))
        except ValueError:
            continue
    if not stats:
        return {"point": np.nan, "ci_low": np.nan, "ci_high": np.nan, "n_valid_boot": 0}
    stats = np.array(stats)
    return {
        "ci_low": float(np.percentile(stats, 100 * alpha / 2)),
        "ci_high": float(np.percentile(stats, 100 * (1 - alpha / 2))),
        "n_valid_boot": int(len(stats)),
    }


def run_spatial_cv(df: pd.DataFrame, feature_cols: list[str], model_name: str, model_factory):
    X = df[feature_cols].to_numpy()
    y = df["outcome"].to_numpy()
    groups = assign_spatial_blocks(df, DEFAULT_BLOCK_SIZE_M)

    n_unique_groups = groups.nunique()
    n_splits = min(N_SPLITS, n_unique_groups, int(y.sum()))  # can't have more folds than positives either
    n_splits = max(n_splits, 2)
    print(f"[{model_name}] using {n_splits} spatial-block folds ({n_unique_groups} unique blocks, {int(y.sum())} positives)")

    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)

    oof_pred = np.full(len(y), np.nan)
    fold_reports = []
    for fold_i, (train_idx, test_idx) in enumerate(skf.split(X, y, groups=groups)):
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X[train_idx])
        X_test = scaler.transform(X[test_idx])
        y_train, y_test = y[train_idx], y[test_idx]

        model = model_factory()
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        oof_pred[test_idx] = proba

        fold_reports.append(
            {
                "fold": fold_i,
                "n_train": len(train_idx),
                "n_test": len(test_idx),
                "n_pos_train": int(y_train.sum()),
                "n_pos_test": int(y_test.sum()),
            }
        )

    valid = ~np.isnan(oof_pred)
    y_valid, pred_valid = y[valid], oof_pred[valid]

    if len(np.unique(y_valid)) < 2:
        print(f"[{model_name}] WARNING: out-of-fold predictions have only one class present - metrics undefined")
        return {"model": model_name, "error": "single_class_oof", "fold_reports": fold_reports}

    pr_auc = average_precision_score(y_valid, pred_valid)
    roc_auc = roc_auc_score(y_valid, pred_valid)
    pred_binary = (pred_valid >= 0.5).astype(int)
    f1 = f1_score(y_valid, pred_binary, zero_division=0)
    bal_acc = balanced_accuracy_score(y_valid, pred_binary)

    pr_auc_ci = bootstrap_ci(average_precision_score, y_valid, pred_valid)
    roc_auc_ci = bootstrap_ci(roc_auc_score, y_valid, pred_valid)

    result = {
        "model": model_name,
        "n_total": len(y),
        "n_valid_oof": int(valid.sum()),
        "n_positive": int(y.sum()),
        "pr_auc": pr_auc,
        "pr_auc_95ci": pr_auc_ci,
        "roc_auc": roc_auc,
        "roc_auc_95ci": roc_auc_ci,
        "f1_at_0.5": f1,
        "balanced_accuracy_at_0.5": bal_acc,
        "fold_reports": fold_reports,
    }
    print(
        f"[{model_name}] PR-AUC={pr_auc:.3f} (95% CI [{pr_auc_ci['ci_low']:.3f}, {pr_auc_ci['ci_high']:.3f}]), "
        f"ROC-AUC={roc_auc:.3f} (95% CI [{roc_auc_ci['ci_low']:.3f}, {roc_auc_ci['ci_high']:.3f}]), "
        f"F1={f1:.3f}, BalAcc={bal_acc:.3f}"
    )
    return result


def build_model_factories(df: pd.DataFrame) -> dict:
    n_pos = int(df["outcome"].sum())
    n_neg = len(df) - n_pos
    models = {
        "logistic_regression": lambda: LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED
        ),
        "random_forest": lambda: RandomForestClassifier(
            n_estimators=300, class_weight="balanced", random_state=RANDOM_SEED, max_depth=5
        ),
    }
    try:
        import xgboost as xgb

        models["xgboost"] = lambda: xgb.XGBClassifier(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            scale_pos_weight=n_neg / n_pos,
            random_state=RANDOM_SEED,
            eval_metric="logloss",
        )
    except ImportError:
        print("[warn] xgboost not available, skipping")

    try:
        import lightgbm as lgb

        models["lightgbm"] = lambda: lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            scale_pos_weight=n_neg / n_pos,
            random_state=RANDOM_SEED,
            verbosity=-1,
        )
    except ImportError:
        print("[warn] lightgbm not available, skipping")
    return models


def main() -> int:
    df = load_primary_dataset()
    print(f"[data] primary Tier A+B dataset: {len(df)} parcels, {int(df['outcome'].sum())} positive (recovery)")

    models = build_model_factories(df)

    # Experiment 10 (feature-group ablation, governing-brief Section AP):
    # three arms run under the IDENTICAL spatial-CV folds/seed for a fair
    # comparison - GIS+Geometric+Environmental+Temporal only (no RS, this
    # is what EXP03-07 in research_log.md already reported before NDVI
    # was available), RS-only (historical NDVI statistics alone), and ALL
    # features combined. This is a real ablation, not the full A-E
    # decomposition the governing protocol sketches (which would separate
    # GIS from Geometric from Environmental individually) - that finer
    # split is a documented further-work item, not silently claimed here.
    feature_sets = {
        "no_RS_gis_geom_env_temporal": FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL,
        "RS_only_historical_ndvi": FEATURE_COLS_RS_ONLY,
        "all_features_RS_plus_GIS_etc": FEATURE_COLS_ALL,
    }

    all_results = {}
    for set_name, cols in feature_sets.items():
        # Drop rows with NaN in THIS feature set's own columns only - e.g.
        # RS-dependent arms lose the Talkha/Sherbin parcels (no Sentinel-2
        # NDVI, a documented limitation - see research_log.md 2026-09-21),
        # but the no-RS arm keeps the full pooled dataset. This is done
        # per-arm, transparently, rather than dropping rows globally.
        df_set = df.dropna(subset=cols).reset_index(drop=True)
        n_dropped = len(df) - len(df_set)
        print(
            f"\n=== Feature set: {set_name} ({len(cols)} features), "
            f"n={len(df_set)} (dropped {n_dropped} rows with missing values in this feature set) ==="
        )
        if int(df_set["outcome"].sum()) < 2:
            print(f"[{set_name}] SKIPPED: fewer than 2 positive cases after dropping NaN rows - cannot run CV")
            continue
        all_results[set_name] = {"n_used": len(df_set), "n_dropped_for_nan": n_dropped}
        for name, factory in models.items():
            all_results[set_name][name] = run_spatial_cv(df_set, cols, f"{set_name}/{name}", factory)

    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    out_path = OUT_METRICS / "baseline_models_spatial_cv.json"
    out_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\n[done] -> {out_path}")

    # Compact ablation summary table (PR-AUC, the primary metric given
    # rare-positive-class prevalence) for quick inspection.
    print("\n=== Ablation summary (PR-AUC) ===")
    for set_name, model_results in all_results.items():
        for model_name, res in model_results.items():
            if model_name in ("n_used", "n_dropped_for_nan") or not isinstance(res, dict):
                continue
            pr_auc = res.get("pr_auc", float("nan"))
            print(f"{set_name:35s} {model_name:20s} PR-AUC={pr_auc:.3f}" if pr_auc == pr_auc else f"{set_name:35s} {model_name:20s} PR-AUC=N/A")

    return 0


if __name__ == "__main__":
    sys.exit(main())
