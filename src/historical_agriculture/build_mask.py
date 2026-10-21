"""Experiment 1: historical agricultural mask (protocol Section 6.1).

A pixel qualifies as historically agricultural if it is classified as
Crops (Esri/IO class 5) in at least 2 of the 3 pre-outcome years
2017-2019 - a repeated-evidence requirement, not a single-year snapshot
(governing-brief Section O: "do not label land agricultural merely
because it appeared green in one image").

Run directly: `python -m src.historical_agriculture.build_mask`
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import rasterio

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"

CROP_CLASS = 5
BASELINE_YEARS = (2017, 2018, 2019)
# Strengthened from 2 to 3 (i.e. ALL baseline years must independently
# agree) following a real, evidence-based finding (research_log.md,
# 2026-09-21 stratified visual validation): multiple parcels admitted by
# the original >=2/3 rule turned out, on Google Earth historical-imagery
# inspection, to have been non-agricultural for years before this
# project's own 2017-2019 baseline window (one case traced back to the
# earliest available imagery, 2007) - i.e. a pixel inconsistently
# classified in the baseline years is exactly the unstable signal that let
# long-standing non-agricultural land into the eligible population. This
# was decided from visual evidence BEFORE any downstream model was
# re-run, per the project's own rule against choosing definitions by
# model performance.
MIN_CROP_YEARS = 3


def load_lulc_stack(window_name: str, years: list[int]):
    stack = []
    profile = None
    for year in years:
        path = DATA_RAW / window_name / "io_lulc" / f"{year}.tif"
        with rasterio.open(path) as src:
            stack.append(src.read(1))
            if profile is None:
                profile = src.profile
    return np.stack(stack, axis=0), profile


def build_historical_mask(window_name: str):
    stack, profile = load_lulc_stack(window_name, list(BASELINE_YEARS))
    is_crop = stack == CROP_CLASS
    crop_year_count = is_crop.sum(axis=0)
    mask = (crop_year_count >= MIN_CROP_YEARS).astype(np.uint8)

    out_path = DATA_PROCESSED / window_name / "historical_agri_mask.tif"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_profile = profile.copy()
    out_profile.update(dtype=np.uint8, count=1, compress="deflate")
    with rasterio.open(out_path, "w", **out_profile) as dst:
        dst.write(mask, 1)

    total = mask.size
    n_agri = int(mask.sum())
    print(
        f"[{window_name}] historical agricultural mask: {n_agri}/{total} px "
        f"({100 * n_agri / total:.1f}%) qualify (>= {MIN_CROP_YEARS}/{len(BASELINE_YEARS)} "
        f"crop years in {BASELINE_YEARS}) -> {out_path}"
    )
    return mask, out_path


def main() -> int:
    import sys as _sys

    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
    from utils.study_area import ALL_WINDOW_NAMES  # noqa: E402

    for window_name in ALL_WINDOW_NAMES:
        build_historical_mask(window_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
