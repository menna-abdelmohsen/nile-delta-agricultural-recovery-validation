"""Sensitivity analysis (protocol Section BN), triggered by a REAL finding:
a 2026-09-21 Google Earth visual spot-check of the highest-confidence
(Tier A) recovery parcel `Mit_Salsil_recovery_33` found NO visual evidence
of vegetation return across four independently-checked dates (2016, 2019,
2021, 2023) plus the latest available imagery (5/27/2025) - the site is
still bare/disturbed/rubble in every view. Tracing the parcel's own real
Esri/IO class sequence explained why: 2017-18 Crops -> 2019-20 Built ->
2021-24 a noisy, spatially patchy 22-65% crop mix that never forms a
coherent majority in any single year, but different scattered pixels each
satisfy the original per-pixel ">=2 consecutive crop years" rule at
DIFFERENT times - so the original majority-vote-of-per-pixel-outcomes
labeling (build_labels.py's classify_trajectory_by_parcel) tipped the
whole parcel to "recovery" from noise, not from a real, spatially
coherent, simultaneous return to cropland.

This module implements and compares a STRICTER, more defensible
alternative: a parcel is only "Observed Recovery" if a SIMULTANEOUS
majority (>= STRICT_MAJORITY_FRACTION) of its own pixels are Crops in the
SAME two consecutive years - not per-pixel-then-aggregate, but
per-YEAR-then-check-majority. This directly targets the failure mode just
found: a parcel with 59% crop in 2023 and 44% crop in 2024 (different,
only partially-overlapping pixel sets) would NOT qualify under this
stricter rule unless the SAME >=50% (or higher) majority of pixels were
crop in both years together.

Run directly: `python -m src.labeling.sensitivity_recovery_definition`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import rasterio

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_LABELS = pathlib.Path(__file__).resolve().parents[2] / "data" / "labels"
OUT_METRICS = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"

CROP_CLASS = 5
YEARS = list(range(2017, 2025))
STRICT_MAJORITY_FRACTIONS = [0.5, 0.7, 0.9, 1.0]  # 1.0 = every single pixel, strictest possible


def load_raster(path: pathlib.Path):
    with rasterio.open(path) as src:
        return src.read(1)


def strict_simultaneous_majority_recovery(window_name: str, majority_fraction: float):
    parcel_id = load_raster(DATA_LABELS / window_name / "parcel_id.tif")
    first_conv_year = load_raster(DATA_LABELS / window_name / "first_conversion_year.tif")
    original_label = load_raster(DATA_LABELS / window_name / "trajectory_label.tif")

    lulc_stack = np.stack(
        [load_raster(DATA_RAW / window_name / "io_lulc" / f"{y}.tif") for y in YEARS], axis=0
    )
    is_crop = lulc_stack == CROP_CLASS

    unique_parcels = np.unique(parcel_id[parcel_id > 0])
    results = {}
    for pid in unique_parcels:
        mask = parcel_id == pid
        conv_year_vals = first_conv_year[mask]
        conv_year = int(np.median(conv_year_vals[conv_year_vals > 0])) if np.any(conv_year_vals > 0) else None
        if conv_year is None:
            continue
        conv_idx = YEARS.index(conv_year) if conv_year in YEARS else None
        if conv_idx is None:
            continue

        n_pixels = int(mask.sum())
        # Fraction of the parcel classified Crops in EACH post-conversion year.
        post_conv_crop_fraction = [
            float(is_crop[t][mask].sum()) / n_pixels for t in range(conv_idx + 1, len(YEARS))
        ]
        # Simultaneous majority in ANY two consecutive years.
        recovered = any(
            post_conv_crop_fraction[i] >= majority_fraction and post_conv_crop_fraction[i + 1] >= majority_fraction
            for i in range(len(post_conv_crop_fraction) - 1)
        )
        original_outcome_vals, original_outcome_freqs = np.unique(original_label[mask], return_counts=True)
        original_outcome = int(original_outcome_vals[np.argmax(original_outcome_freqs)])

        results[int(pid)] = {
            "n_pixels": n_pixels,
            "conversion_year": conv_year,
            "post_conversion_crop_fraction_by_year": post_conv_crop_fraction,
            "strict_recovery": bool(recovered),
            "original_label_recovery": original_outcome == 1,
        }
    return results


def main() -> int:
    all_results = {}
    for window_name in ("El-Bagalat", "Mit_Salsil"):
        for frac in STRICT_MAJORITY_FRACTIONS:
            key = f"{window_name}_majority_{frac}"
            parcels = strict_simultaneous_majority_recovery(window_name, frac)
            n_strict_recovery = sum(1 for p in parcels.values() if p["strict_recovery"])
            n_original_recovery = sum(1 for p in parcels.values() if p["original_label_recovery"])
            n_agree = sum(
                1 for p in parcels.values() if p["strict_recovery"] == p["original_label_recovery"]
            )
            all_results[key] = {
                "majority_fraction_required": frac,
                "n_parcels_total": len(parcels),
                "n_strict_recovery": n_strict_recovery,
                "n_original_label_recovery": n_original_recovery,
                "n_agree_with_original": n_agree,
            }
            print(
                f"[{window_name}, majority>={frac}] strict_recovery={n_strict_recovery}, "
                f"original_recovery={n_original_recovery}, agree={n_agree}/{len(parcels)}"
            )

    # Specifically re-check the parcel that triggered this whole analysis.
    ms_parcels = strict_simultaneous_majority_recovery("Mit_Salsil", 0.5)
    target = ms_parcels.get(33)
    print(f"\nMit_Salsil_recovery_33 (parcel_id=33) under strict 50% simultaneous-majority rule: {target}")

    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    out_path = OUT_METRICS / "sensitivity_recovery_definition.json"
    out_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\n[done] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
