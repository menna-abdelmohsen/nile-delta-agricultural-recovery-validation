"""Experiment 2c: assign label-confidence tiers (protocol Section 6.4) using
the real WorldCover corroboration computed in verify_against_worldcover.py.

Per-pixel rule (independent of trajectory stage - checks whether WorldCover
corroborates whatever class the IO-LULC product ITSELF claims for that
pixel in each WorldCover-covered year, 2020 and 2021):
  - Tier A (high confidence): WorldCover agrees with the IO-claimed class
    in BOTH 2020 and 2021 (where the pixel's IO class in those years is
    unambiguously crop or built/bare - "n/a" if the IO class that year is
    something else, e.g. water/trees/rangeland, in which case that year
    cannot corroborate and is excluded from the tier decision for that
    pixel).
  - Tier B (medium confidence): WorldCover agrees in exactly one
    corroborable year, or only one year is corroborable at all.
  - Tier C (low/uncertain): WorldCover disagrees in every corroborable
    year, or no year is corroborable (pixel's post-conversion trajectory
    never touches 2020/2021, or the IO class those years is not crop/built).

This is a real, data-driven tiering - not asserted. The resulting tier
counts are the honest answer to "is the recovery target empirically
validated?" (protocol Section 1, Q7) for THIS pipeline's candidate events.

Run directly: `python -m src.labeling.assign_confidence_tiers`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from verify_against_worldcover import (  # noqa: E402
    IO_BUILT_OR_BARE,
    IO_CROPLAND,
    WC_BUILTUP,
    WC_CROPLAND,
    reproject_worldcover_to_lulc_grid,
)

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_LABELS = pathlib.Path(__file__).resolve().parents[2] / "data" / "labels"


def load_raster(path: pathlib.Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def per_year_corroboration(io_arr: np.ndarray, wc_arr: np.ndarray) -> np.ndarray:
    """Return int8 array: 1 = corroborated (IO class is crop/built AND
    WorldCover agrees), 0 = contradicted (IO class is crop/built but
    WorldCover disagrees), -1 = not corroborable this year (IO class isn't
    crop or built/bare here, so WorldCover's agreement/disagreement with a
    *different* scheme's classes isn't a meaningful check)."""
    out = np.full(io_arr.shape, -1, dtype=np.int8)
    io_is_crop = io_arr == IO_CROPLAND
    io_is_built = np.isin(io_arr, IO_BUILT_OR_BARE)
    out[io_is_crop & (wc_arr == WC_CROPLAND)] = 1
    out[io_is_crop & (wc_arr != WC_CROPLAND)] = 0
    out[io_is_built & (wc_arr == WC_BUILTUP)] = 1
    out[io_is_built & (wc_arr != WC_BUILTUP)] = 0
    return out


def assign_tiers(window_name: str):
    lulc_2020 = load_raster(DATA_RAW / window_name / "io_lulc" / "2020.tif")
    lulc_2021 = load_raster(DATA_RAW / window_name / "io_lulc" / "2021.tif")
    wc_2020 = reproject_worldcover_to_lulc_grid(window_name, 2020)
    wc_2021 = reproject_worldcover_to_lulc_grid(window_name, 2021)

    corrob_2020 = per_year_corroboration(lulc_2020, wc_2020)
    corrob_2021 = per_year_corroboration(lulc_2021, wc_2021)

    trajectory_label = load_raster(DATA_LABELS / window_name / "trajectory_label.tif")

    tier = np.full(trajectory_label.shape, "N", dtype="<U1")  # N = not applicable (not converted)
    is_event = np.isin(trajectory_label, [0, 1])

    for r in range(trajectory_label.shape[0]):
        for c in range(trajectory_label.shape[1]):
            if not is_event[r, c]:
                continue
            votes = [v for v in (corrob_2020[r, c], corrob_2021[r, c]) if v != -1]
            if len(votes) == 0:
                tier[r, c] = "C"
            elif len(votes) == 2 and all(v == 1 for v in votes):
                tier[r, c] = "A"
            elif any(v == 1 for v in votes):
                tier[r, c] = "B"
            else:
                tier[r, c] = "C"

    # Event-level tier: the MODE tier among a PARCEL's pixels, using the
    # fixed parcel_id assigned at MMU-detection time (build_labels.py) -
    # never re-derived from the outcome mask, to avoid the sub-MMU
    # fragmentation bug caught and fixed in that module (2026-09-20).
    parcel_id = load_raster(DATA_LABELS / window_name / "parcel_id.tif")

    def parcel_tier_counts(label_value: int):
        unique_parcels = np.unique(parcel_id[parcel_id > 0])
        counts = {"A": 0, "B": 0, "C": 0}
        n_events = 0
        for pid in unique_parcels:
            mask = parcel_id == pid
            outcome_vals, outcome_freqs = np.unique(trajectory_label[mask], return_counts=True)
            parcel_outcome = outcome_vals[np.argmax(outcome_freqs)]
            if parcel_outcome != label_value:
                continue
            n_events += 1
            comp_tiers = tier[mask]
            vals, freqs = np.unique(comp_tiers, return_counts=True)
            mode_tier = vals[np.argmax(freqs)]
            if mode_tier in counts:
                counts[mode_tier] += 1
        return counts, n_events

    recovery_tiers, n_recovery_events = parcel_tier_counts(1)
    persistent_tiers, n_persistent_events = parcel_tier_counts(0)

    out_path = DATA_LABELS / window_name / "label_confidence_tier.tif"
    with rasterio.open(DATA_LABELS / window_name / "trajectory_label.tif") as ref:
        profile = ref.profile
    tier_numeric = np.select(
        [tier == "A", tier == "B", tier == "C"], [2, 1, 0], default=-1
    ).astype(np.int8)
    out_profile = profile.copy()
    out_profile.update(dtype=np.int8, count=1, compress="deflate")
    with rasterio.open(out_path, "w", **out_profile) as dst:
        dst.write(tier_numeric, 1)

    result = {
        "window": window_name,
        "n_recovery_events_total": n_recovery_events,
        "recovery_events_by_tier": recovery_tiers,
        "n_persistent_events_total": n_persistent_events,
        "persistent_events_by_tier": persistent_tiers,
    }
    print(f"[{window_name}] {json.dumps(result, indent=2)}")
    return result


def main() -> int:
    import sys as _sys

    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
    from utils.study_area import ALL_WINDOW_NAMES  # noqa: E402

    all_results = {}
    for window_name in ALL_WINDOW_NAMES:
        all_results[window_name] = assign_tiers(window_name)
    out_path = DATA_LABELS / "label_confidence_tiers_all_windows.json"
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"[done] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
