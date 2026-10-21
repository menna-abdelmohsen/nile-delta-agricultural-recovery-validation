"""Final quality-assurance audit (governing-brief Section 25 / user
instruction #25): checks that must pass before any result is treated as
final. Each check either passes with a printed confirmation or raises/
prints a clear failure - this script does not silently continue past a
real problem.

Run directly: `python -m src.utils.qa_audit`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOW_NAMES  # noqa: E402

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
DATA_LABELS = pathlib.Path(__file__).resolve().parents[2] / "data" / "labels"

CHECKS_PASSED = []
CHECKS_FAILED = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        CHECKS_PASSED.append(name)
        print(f"[PASS] {name} {('- ' + detail) if detail else ''}")
    else:
        CHECKS_FAILED.append((name, detail))
        print(f"[FAIL] {name} - {detail}")


def audit_crs_consistency():
    crs_set = set()
    for window in ALL_WINDOW_NAMES:
        for path in (DATA_RAW / window / "io_lulc").glob("*.tif"):
            with rasterio.open(path) as src:
                crs_set.add(str(src.crs))
    check("CRS consistency across all io_lulc rasters, all windows", len(crs_set) == 1, f"found: {crs_set}")


def audit_no_future_leakage_in_conversion_year():
    """A parcel's recorded conversion_year must never be later than
    2024 (last available year) and must be a year that actually appears
    in the label record - a basic sanity bound, not a full leakage proof
    (the real leakage audit is structural: features are computed only
    from years <= conversion_year, enforced by construction in
    build_master_dataset.py, not re-derived here)."""
    df = pd.read_csv(DATA_PROCESSED / "master_dataset_all_windows.csv")
    valid_years = df["conversion_year"].between(2017, 2024).all()
    check(
        "All conversion_year values within [2017, 2024]",
        bool(valid_years),
        f"range found: {df['conversion_year'].min()}-{df['conversion_year'].max()}",
    )
    # Structural leakage check: years_since_conversion must be non-negative
    # (a parcel cannot have "recovered" before it converted).
    non_negative = (df["years_since_conversion"] >= 0).all()
    check("years_since_conversion always >= 0 (no reversed time order)", bool(non_negative))


def audit_label_integrity():
    df = pd.read_csv(DATA_PROCESSED / "master_dataset_all_windows.csv")
    check("No duplicate event_id", df["event_id"].is_unique, f"n rows={len(df)}, n unique={df['event_id'].nunique()}")
    check("outcome is binary {0,1} only", set(df["outcome"].unique()) <= {0, 1})
    check("label_confidence_tier is one of {A,B,C}", set(df["label_confidence_tier"].unique()) <= {"A", "B", "C"})
    non_ndvi_cols = [
        c for c in df.columns
        if ("agri_fraction" in c or "builtup_fraction" in c or "distance_to" in c or c in ("area_m2", "perimeter_m", "compactness", "mean_elevation_m"))
    ]
    check("No missing values in non-NDVI core feature columns", not df[non_ndvi_cols].isna().any().any())
    # NDVI missingness for Talkha/Sherbin is a documented, accepted limitation
    # (research_log.md, 2026-09-21) - not a bug, so checked separately and
    # expected to show exactly the two affected windows, nothing else.
    ndvi_missing_windows = set(df[df["historical_ndvi_mean"].isna()]["window"].unique())
    check(
        "NDVI missingness confined to the two documented windows only (Talkha, Sherbin)",
        ndvi_missing_windows <= {"Talkha", "Sherbin"},
        f"windows with missing NDVI: {ndvi_missing_windows}",
    )


def audit_spatial_alignment():
    """Confirm the parcel_id, trajectory_label, and first_conversion_year
    rasters share identical shape/transform per window (a structural
    prerequisite for every per-parcel feature computed by indexing them
    together)."""
    for window in ALL_WINDOW_NAMES:
        label_dir = DATA_LABELS / window
        profiles = {}
        for name in ("parcel_id", "trajectory_label", "first_conversion_year"):
            with rasterio.open(label_dir / f"{name}.tif") as src:
                profiles[name] = (src.shape, src.transform)
        shapes = {p[0] for p in profiles.values()}
        transforms = {p[1] for p in profiles.values()}
        check(
            f"{window}: parcel_id/trajectory_label/first_conversion_year share grid",
            len(shapes) == 1 and len(transforms) == 1,
            f"shapes={shapes}",
        )


def audit_geographic_separation():
    """Confirm the 4 study windows do not spatially overlap (a
    prerequisite for treating them as geographically distinct blocks in
    any leave-one-region-out analysis)."""
    from utils.study_area import ALL_WINDOWS

    boxes = [(w.name, w.min_lon, w.max_lon, w.min_lat, w.max_lat) for w in ALL_WINDOWS]
    overlaps = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            n1, minx1, maxx1, miny1, maxy1 = boxes[i]
            n2, minx2, maxx2, miny2, maxy2 = boxes[j]
            overlap = not (maxx1 < minx2 or maxx2 < minx1 or maxy1 < miny2 or maxy2 < miny1)
            if overlap:
                overlaps.append((n1, n2))
    check("No spatial overlap between the 4 study windows", len(overlaps) == 0, f"overlaps: {overlaps}")


def audit_experiment_registry_traceability():
    registry_path = pathlib.Path(__file__).resolve().parents[2] / "protocol" / "experiment_registry.csv"
    df = pd.read_csv(registry_path)
    executed = df[df["status"] == "EXECUTED"]
    missing_output = executed[executed["output_paths"].isna() | (executed["output_paths"] == "")]
    check(
        "Every EXECUTED experiment has a non-empty output_paths field",
        len(missing_output) == 0,
        f"{len(missing_output)} EXECUTED rows missing output_paths" if len(missing_output) else "",
    )


def main() -> int:
    print("=== QA Audit ===\n")
    audit_crs_consistency()
    audit_no_future_leakage_in_conversion_year()
    audit_label_integrity()
    audit_spatial_alignment()
    audit_geographic_separation()
    audit_experiment_registry_traceability()

    print(f"\n=== Summary: {len(CHECKS_PASSED)} passed, {len(CHECKS_FAILED)} failed ===")
    if CHECKS_FAILED:
        print("FAILED CHECKS:")
        for name, detail in CHECKS_FAILED:
            print(f"  - {name}: {detail}")

    out_path = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics" / "qa_audit_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"passed": CHECKS_PASSED, "failed": CHECKS_FAILED}, indent=2, default=str)
    )
    print(f"\n[done] -> {out_path}")
    return 0 if not CHECKS_FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
