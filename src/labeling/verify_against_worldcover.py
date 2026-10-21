"""Experiment 2b: independent label verification against ESA WorldCover
(protocol Section 6.4, Tier A/B/C confidence assignment).

ESA WorldCover is only available for 2020 and 2021 - so this check can
only confirm/contradict the IO-LULC-derived class for pixels in those two
specific years, not the whole 2017-2024 record. That is a real, stated
constraint, not a shortcut: it is exactly the same constraint Paper 2
operated under (its Table III agreement check also only covered 2020/2021).

WorldCover was downloaded on its own native grid (960x1092 px, since its
tiling/offset differs from the IO-LULC product's 897x878 px grid over the
same lon/lat window) - so this script reprojects/resamples WorldCover onto
the IO-LULC grid (nearest-neighbour, appropriate for categorical data)
before comparing pixel-to-pixel. This alignment step was flagged as
necessary in research_log.md when the rasters were first fetched; this is
where it is actually done.

WorldCover class codes (10=Tree, 20=Shrubland, 30=Grassland, 40=Cropland,
50=Built-up, 60=Bare/sparse veg, 80=Water, 90=Wetland - per ESA's
published legend).

Run directly: `python -m src.labeling.verify_against_worldcover`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_LABELS = pathlib.Path(__file__).resolve().parents[2] / "data" / "labels"

WC_CROPLAND = 40
WC_BUILTUP = 50
IO_CROPLAND = 5
IO_BUILT_OR_BARE = (7, 8)


def reproject_worldcover_to_lulc_grid(window_name: str, wc_year: int):
    wc_path = DATA_RAW / window_name / "esa_worldcover" / f"{wc_year}.tif"
    lulc_ref_path = DATA_RAW / window_name / "io_lulc" / "2017.tif"

    with rasterio.open(lulc_ref_path) as ref:
        ref_transform, ref_crs, ref_shape = ref.transform, ref.crs, (ref.height, ref.width)

    with rasterio.open(wc_path) as src:
        dst = np.zeros(ref_shape, dtype=src.dtypes[0])
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            resampling=Resampling.nearest,
        )
    return dst


def load_raster(path: pathlib.Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def verify_window(window_name: str):
    lulc_2020 = load_raster(DATA_RAW / window_name / "io_lulc" / "2020.tif")
    lulc_2021 = load_raster(DATA_RAW / window_name / "io_lulc" / "2021.tif")
    wc_2020 = reproject_worldcover_to_lulc_grid(window_name, 2020)
    wc_2021 = reproject_worldcover_to_lulc_grid(window_name, 2021)

    trajectory_label = load_raster(DATA_LABELS / window_name / "trajectory_label.tif")
    first_conv_year = load_raster(DATA_LABELS / window_name / "first_conversion_year.tif")

    def builtup_iou(io_arr, wc_arr):
        io_built = np.isin(io_arr, IO_BUILT_OR_BARE)
        wc_built = wc_arr == WC_BUILTUP
        intersection = np.logical_and(io_built, wc_built).sum()
        union = np.logical_or(io_built, wc_built).sum()
        return float(intersection / union) if union > 0 else float("nan")

    def cropland_iou(io_arr, wc_arr):
        io_crop = io_arr == IO_CROPLAND
        wc_crop = wc_arr == WC_CROPLAND
        intersection = np.logical_and(io_crop, wc_crop).sum()
        union = np.logical_or(io_crop, wc_crop).sum()
        return float(intersection / union) if union > 0 else float("nan")

    product_agreement = {
        "2020": {"builtup_iou": builtup_iou(lulc_2020, wc_2020), "cropland_iou": cropland_iou(lulc_2020, wc_2020)},
        "2021": {"builtup_iou": builtup_iou(lulc_2021, wc_2021), "cropland_iou": cropland_iou(lulc_2021, wc_2021)},
    }

    # Event-level check: for recovery-labeled pixels whose conversion year is
    # such that 2020 or 2021 falls within their post-conversion, pre-recovery
    # OR post-recovery window, does WorldCover agree with the IO-derived
    # class in that specific year? This is necessarily partial coverage
    # (only pixels whose relevant year is 2020/2021 can be checked at all).
    def event_level_check(label_value: int, io_stack_year, wc_year_arr, io_year_arr, io_expect_built: bool):
        mask = trajectory_label == label_value
        n_checkable = int(mask.sum())
        if n_checkable == 0:
            return {"n_checkable_pixels": 0, "n_agree": 0, "agreement_rate": None}
        io_class_is_built = np.isin(io_year_arr, IO_BUILT_OR_BARE)
        wc_class_is_built = wc_year_arr == WC_BUILTUP
        if io_expect_built:
            agree = mask & io_class_is_built & wc_class_is_built
        else:
            wc_class_is_crop = wc_year_arr == WC_CROPLAND
            io_class_is_crop = io_year_arr == IO_CROPLAND
            agree = mask & io_class_is_crop & wc_class_is_crop
        n_agree = int(agree.sum())
        return {
            "n_checkable_pixels": n_checkable,
            "n_agree_pixels": n_agree,
            "agreement_rate": n_agree / n_checkable if n_checkable else None,
        }

    # For persistent-conversion pixels (label==0), check 2020 and 2021 both
    # expect "built/bare" per the IO trajectory - do these years agree with
    # WorldCover's built-up class at those same pixels?
    persistent_check_2020 = event_level_check(0, None, wc_2020, lulc_2020, io_expect_built=True)
    persistent_check_2021 = event_level_check(0, None, wc_2021, lulc_2021, io_expect_built=True)

    # For recovery pixels, whether 2020/2021 corresponds to their pre- or
    # post-recovery state varies per pixel (conversion years differ), so a
    # single "expect built" or "expect crop" assumption is NOT valid across
    # all recovery pixels simultaneously. Instead, cross-check WorldCover's
    # class against whatever the IO product itself says for that exact
    # pixel/year - i.e. does WorldCover corroborate the IO label AT ALL,
    # regardless of which trajectory stage it falls in.
    def raw_corroboration(label_value: int):
        mask = trajectory_label == label_value
        results = {}
        for year, io_arr, wc_arr in ((2020, lulc_2020, wc_2020), (2021, lulc_2021, wc_2021)):
            sub_io = io_arr[mask]
            sub_wc = wc_arr[mask]
            crop_agree = np.logical_and(sub_io == IO_CROPLAND, sub_wc == WC_CROPLAND).sum()
            built_agree = np.logical_and(np.isin(sub_io, IO_BUILT_OR_BARE), sub_wc == WC_BUILTUP).sum()
            n = mask.sum()
            results[str(year)] = {
                "n_pixels": int(n),
                "n_crop_class_agree": int(crop_agree),
                "n_built_class_agree": int(built_agree),
                "n_disagree_or_other": int(n - crop_agree - built_agree),
            }
        return results

    recovery_corroboration = raw_corroboration(1)
    persistent_corroboration = raw_corroboration(0)

    result = {
        "window": window_name,
        "product_agreement_wholewindow": product_agreement,
        "recovery_pixel_corroboration_by_year": recovery_corroboration,
        "persistent_pixel_corroboration_by_year": persistent_corroboration,
    }
    print(f"[{window_name}] {json.dumps(result, indent=2)}")
    return result


def main() -> int:
    import sys as _sys

    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
    from utils.study_area import ALL_WINDOW_NAMES  # noqa: E402

    all_results = {}
    for window_name in ALL_WINDOW_NAMES:
        all_results[window_name] = verify_window(window_name)

    out_path = DATA_LABELS / "worldcover_verification.json"
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"[done] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
