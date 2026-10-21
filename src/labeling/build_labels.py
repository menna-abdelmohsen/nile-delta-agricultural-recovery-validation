"""Experiment 2: conversion detection + trajectory classification into
Observed Recovery (Y=1) vs Persistent Conversion (Y=0) - protocol Sections
6.2-6.3. Built independently from Paper 2's specific reversal candidates,
per the user's explicit direction (2026-09-20) - only the definitional
logic (MMU, persistence windows) is kept comparable, not the data itself.

Definitions (see protocol/phase1_protocol.md Section 6 for the full
rationale):
  - A pixel is in the at-risk population if it is in the historical
    agricultural mask (build_mask.py) and never Water.
  - A pixel registers a CONVERSION at year t if: classified Crops (5) at
    year t-1 (or, more generally, was in the at-risk historical-agri set),
    classified Built (7) or Bare (8) at year t, and remains in {Built,
    Bare} for at least 1 further year (t+1) - "1-year persistence".
  - MMU: the conversion must belong to a 4-connected component of >= 18
    pixels (1,800 sq m at 10 m resolution - same real-world MMU as Paper
    2's 30 m/2-cell rule, expressed in this project's native 10 m grid).
  - Once a pixel registers a conversion it exits the at-risk population
    permanently (first-occurrence design, matching Paper 2's convention
    for comparability) - only the FIRST qualifying conversion year is used.
  - OBSERVED RECOVERY (Y=1): after conversion, the pixel returns to Crops
    (5) for >= 2 CONSECUTIVE years at any point before the end of the
    available record (2024).
  - PERSISTENT CONVERSION (Y=0): the pixel remains in {Built, Bare}
    (or any non-Crops class) through the end of the record without ever
    meeting the Y=1 criterion.
  - EXCLUDED: single-year returns to Crops that never reach 2 consecutive
    years (ambiguous - logged separately, not silently dropped).

Run directly: `python -m src.labeling.build_labels`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
DATA_LABELS = pathlib.Path(__file__).resolve().parents[2] / "data" / "labels"

CROP_CLASS = 5
WATER_CLASS = 1
NON_AGRI_CLASSES = (7, 8)  # Built, Bare
YEARS = list(range(2017, 2025))  # 2017-2024, all available years
MIN_MMU_PIXELS = 18  # 1,800 sq m at 10 m resolution
RECOVERY_MIN_CONSECUTIVE_YEARS = 2
CONVERSION_PERSISTENCE_YEARS = 1
# Primary recovery rule, per the real, evidence-driven decision recorded in
# research_log.md (2026-09-21): a parcel is only "Observed Recovery" if a
# SIMULTANEOUS majority of its OWN pixels are Crops in the SAME two
# consecutive years - not the original per-pixel-then-aggregate rule,
# which was shown (via Google Earth historical-imagery inspection of
# Mit_Salsil_recovery_33) to let spatially incoherent, temporally
# staggered classification noise tip a parcel to "recovery" with no real,
# coherent return to cropland. This threshold (0.5) was chosen from
# independent visual evidence and the sensitivity-analysis comparison
# (src/labeling/sensitivity_recovery_definition.py), NOT from downstream
# model performance.
RECOVERY_SIMULTANEOUS_MAJORITY_FRACTION = 0.5


def load_lulc_stack(window_name: str):
    stack = []
    profile = None
    for year in YEARS:
        path = DATA_RAW / window_name / "io_lulc" / f"{year}.tif"
        with rasterio.open(path) as src:
            stack.append(src.read(1))
            if profile is None:
                profile = src.profile
    return np.stack(stack, axis=0), profile  # shape (n_years, H, W)


def load_historical_mask(window_name: str) -> np.ndarray:
    path = DATA_PROCESSED / window_name / "historical_agri_mask.tif"
    with rasterio.open(path) as src:
        return src.read(1)


def find_first_conversion_year(stack: np.ndarray, historical_mask: np.ndarray):
    """For each pixel, find the index (into YEARS) of its first qualifying
    conversion year, or -1 if none, AND a stable `parcel_id` raster
    identifying which originally-detected, MMU-qualifying connected
    component each converted pixel belongs to.

    The parcel_id is fixed at the moment a component first passes the MMU
    filter and is NEVER re-derived later from a downstream mask (e.g. the
    outcome/trajectory label) - this is deliberate: re-deriving connected
    components from a per-pixel outcome label after the fact can fragment
    one physical MMU-qualifying parcel into several sub-MMU pieces if
    pixels within it end up with different trajectory outcomes (some
    recover, some don't). That fragmentation was caught during data
    quality control (2026-09-20 - a batch of "events" with area_px as low
    as 1 and compactness pinned at exactly 4*pi, a mathematical signature
    of a degenerate single/few-pixel shape) and is fixed here by making
    the ORIGINAL MMU-qualifying patch the permanent analysis unit; its
    outcome is then decided by majority vote over its own pixels
    (see classify_trajectory_by_parcel), never by re-clustering pixels
    that happen to share an outcome value.
    """
    n_years, h, w = stack.shape
    first_conv_idx = np.full((h, w), -1, dtype=np.int16)
    parcel_id = np.zeros((h, w), dtype=np.int32)
    already_converted = np.zeros((h, w), dtype=bool)
    next_parcel_id = 1

    is_nonagri = np.isin(stack, NON_AGRI_CLASSES)

    for t in range(1, n_years - CONVERSION_PERSISTENCE_YEARS):
        prev_is_agri_eligible = historical_mask.astype(bool) & ~already_converted
        becomes_nonagri = is_nonagri[t]
        persists = np.all(is_nonagri[t : t + 1 + CONVERSION_PERSISTENCE_YEARS], axis=0)
        candidate = prev_is_agri_eligible & becomes_nonagri & persists

        # MMU filter: connected-component size >= MIN_MMU_PIXELS on this
        # year's candidate mask (4-connectivity). This is the ONLY place
        # component identity is assigned - it is never recomputed later.
        labeled, n_components = ndimage.label(candidate, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
        if n_components > 0:
            sizes = ndimage.sum(candidate, labeled, index=np.arange(1, n_components + 1))
            valid_component_ids = np.where(sizes >= MIN_MMU_PIXELS)[0] + 1
        else:
            valid_component_ids = np.array([], dtype=int)

        for comp_local_id in valid_component_ids:
            comp_mask = (labeled == comp_local_id) & (first_conv_idx == -1)
            if not comp_mask.any():
                continue
            first_conv_idx[comp_mask] = t
            parcel_id[comp_mask] = next_parcel_id
            next_parcel_id += 1
        already_converted |= first_conv_idx >= 0

    return first_conv_idx, parcel_id


def classify_trajectory_by_parcel(stack: np.ndarray, first_conv_idx: np.ndarray, parcel_id: np.ndarray):
    """Classify each PARCEL's (not each pixel's) post-conversion
    trajectory as recovery (1) or persistent (0), using the SIMULTANEOUS
    majority rule (see RECOVERY_SIMULTANEOUS_MAJORITY_FRACTION docstring
    above): a parcel is "Observed Recovery" only if, in some pair of
    consecutive post-conversion years, at least that fraction of the
    SAME parcel's pixels are Crops in BOTH years together - not decided
    per-pixel-then-aggregated, which was shown to be exploitable by
    spatially incoherent, temporally staggered classification noise
    (research_log.md, 2026-09-21).

    A parcel with no post-conversion years available (converted too close
    to the end of the record) is excluded (-1), not silently counted as
    persistent."""
    n_years, h, w = stack.shape
    is_crop = stack == CROP_CLASS
    final_label = np.full((h, w), -9, dtype=np.int8)  # -9 = never converted

    unique_parcels = np.unique(parcel_id[parcel_id > 0])
    for pid in unique_parcels:
        mask = parcel_id == pid
        conv_idx_vals = first_conv_idx[mask]
        conv_idx_vals = conv_idx_vals[conv_idx_vals >= 0]
        if conv_idx_vals.size == 0:
            continue
        t0 = int(np.median(conv_idx_vals))
        n_pixels = int(mask.sum())

        post_conv_crop_fraction = [
            float(is_crop[t][mask].sum()) / n_pixels for t in range(t0 + 1, n_years)
        ]
        if len(post_conv_crop_fraction) == 0:
            final_label[mask] = -1
            continue

        recovered = any(
            post_conv_crop_fraction[i] >= RECOVERY_SIMULTANEOUS_MAJORITY_FRACTION
            and post_conv_crop_fraction[i + 1] >= RECOVERY_SIMULTANEOUS_MAJORITY_FRACTION
            for i in range(len(post_conv_crop_fraction) - 1)
        )
        final_label[mask] = 1 if recovered else 0

    return final_label


def run_for_window(window_name: str):
    stack, profile = load_lulc_stack(window_name)
    historical_mask = load_historical_mask(window_name)

    first_conv_idx, parcel_id = find_first_conversion_year(stack, historical_mask)
    trajectory_label = classify_trajectory_by_parcel(stack, first_conv_idx, parcel_id)

    out_dir = DATA_LABELS / window_name
    out_dir.mkdir(parents=True, exist_ok=True)

    conv_year_raster = np.where(
        first_conv_idx >= 0, np.array(YEARS, dtype=np.int16)[np.clip(first_conv_idx, 0, len(YEARS) - 1)], 0
    ).astype(np.int16)

    for name, arr, dtype in (
        ("first_conversion_year", conv_year_raster, np.int16),
        ("trajectory_label", trajectory_label, np.int8),
        ("parcel_id", parcel_id, np.int32),
    ):
        out_path = out_dir / f"{name}.tif"
        out_profile = profile.copy()
        out_profile.update(dtype=dtype, count=1, compress="deflate", nodata=None)
        with rasterio.open(out_path, "w", **out_profile) as dst:
            dst.write(arr.astype(dtype), 1)

    n_converted = int((first_conv_idx >= 0).sum())
    n_recovery = int((trajectory_label == 1).sum())
    n_persistent = int((trajectory_label == 0).sum())
    n_excluded = int((trajectory_label == -1).sum())

    # PARCEL-level event counts, using the fixed parcel_id assigned at MMU
    # detection time (never re-derived from the outcome mask - see
    # docstring of find_first_conversion_year for why that matters).
    unique_parcels = np.unique(parcel_id[parcel_id > 0])
    parcel_outcomes = {}
    for pid in unique_parcels:
        mask = parcel_id == pid
        vals, counts = np.unique(trajectory_label[mask], return_counts=True)
        parcel_outcomes[int(pid)] = int(vals[np.argmax(counts)])
    n_recovery_events = sum(1 for v in parcel_outcomes.values() if v == 1)
    n_persistent_events = sum(1 for v in parcel_outcomes.values() if v == 0)
    n_excluded_events = sum(1 for v in parcel_outcomes.values() if v not in (0, 1))

    summary = {
        "window": window_name,
        "years_covered": YEARS,
        "n_pixels_converted_total": n_converted,
        "n_pixels_recovery": n_recovery,
        "n_pixels_persistent": n_persistent,
        "n_pixels_excluded_indeterminate": n_excluded,
        "n_parcel_recovery_EVENTS": n_recovery_events,
        "n_parcel_persistent_EVENTS": n_persistent_events,
        "n_parcel_excluded_EVENTS": n_excluded_events,
        "n_parcels_total": int(len(unique_parcels)),
        "mmu_pixels": MIN_MMU_PIXELS,
        "recovery_min_consecutive_years": RECOVERY_MIN_CONSECUTIVE_YEARS,
    }
    print(f"[{window_name}] {json.dumps(summary, indent=2)}")

    summary_path = out_dir / "label_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    import sys as _sys

    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
    from utils.study_area import ALL_WINDOW_NAMES  # noqa: E402

    all_summaries = {}
    for window_name in ALL_WINDOW_NAMES:
        all_summaries[window_name] = run_for_window(window_name)

    combined_path = DATA_LABELS / "label_summary_all_windows.json"
    combined_path.write_text(json.dumps(all_summaries, indent=2))
    print(f"[done] combined summary -> {combined_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
