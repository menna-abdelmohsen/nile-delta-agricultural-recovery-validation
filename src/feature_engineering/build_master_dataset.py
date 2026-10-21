"""Build the master parcel/event-level ML dataset (governing-brief Section
AB), one row per connected-component conversion event (recovery or
persistent), from real, already-EXECUTED pipeline outputs:
  - data/labels/{window}/trajectory_label.tif        (EXP02)
  - data/labels/{window}/first_conversion_year.tif   (EXP02)
  - data/labels/{window}/label_confidence_tier.tif   (EXP02c)
  - data/processed/{window}/historical_agri_mask.tif (EXP01)
  - data/raw/{window}/io_lulc/*.tif                  (public COG pull)
  - data/raw/{window}/dem/elevation.tif              (public COG pull)
  - data/raw/{window}/osm_roads/roads.geojson         (Overpass pull)
  - data/raw/{window}/sentinel2_ndvi/*.tif           (STAC pull, if present
    at run time - features that need it are computed only for years whose
    composite actually exists on disk; missing years are left as NaN and
    reported, never silently zero-filled)

Feature groups implemented here (see protocol/phase1_protocol.md Section 7
for the full rationale of each):
  1. Historical agricultural strength: fraction of 2017-2019 classified
     Crops at the event's pixels (from the historical mask build) - this
     is available NOW without Sentinel-2; NDVI-based statistics (mean/max/
     std of growing-season NDVI over 2017-2019) are ADDED once the S2
     pull for those years exists on disk.
  2. Temporal conversion characteristics: conversion year, years-since-
     conversion (relative to the last observed year, 2024).
  3. GIS/spatial: distance from the event centroid to the nearest
     currently-agricultural pixel (outside the event itself) and to the
     nearest OSM road, computed in the study CRS.
  4. Geometric: pixel-count area, perimeter (via boundary pixel count
     approximation), compactness (Polsby-Popper-style ratio).
  5. Environmental: mean elevation and slope-proxy (local elevation range)
     under the event footprint, from the real Copernicus DEM pull.

Run directly: `python -m src.feature_engineering.build_master_dataset`
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy
from scipy import ndimage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

DATA_RAW = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
DATA_LABELS = pathlib.Path(__file__).resolve().parents[2] / "data" / "labels"
OUT_DIR = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"

STRUCT4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
CROP_CLASS = 5


def load_raster(path: pathlib.Path):
    with rasterio.open(path) as src:
        return src.read(1), src.transform, src.crs


def sample_raster_at_pixels(raster: np.ndarray, raster_transform, rows_px, cols_px, source_transform):
    """Sample `raster` (on its OWN grid/transform) at the real-world
    locations implied by (rows_px, cols_px) on a DIFFERENT grid
    (source_transform) - needed because the DEM (30 m) and the
    LULC/label rasters (10 m) do not share a pixel grid even though they
    cover the same geographic window. Out-of-bounds indices (from
    floating-point edge effects at the window boundary) are clipped
    rather than raising, since they represent at most a fraction of a
    30 m pixel of real displacement."""
    xs, ys = xy(source_transform, rows_px, cols_px)
    dem_rows, dem_cols = rasterio.transform.rowcol(raster_transform, xs, ys)
    dem_rows = np.clip(np.array(dem_rows), 0, raster.shape[0] - 1)
    dem_cols = np.clip(np.array(dem_cols), 0, raster.shape[1] - 1)
    return raster[dem_rows, dem_cols]


def parcel_geometry_features(parcel_id: np.ndarray, outcome_mask: np.ndarray, transform, pixel_size_m: float):
    """One row per PARCEL (fixed at MMU-detection time in build_labels.py),
    restricted to parcels whose majority outcome matches outcome_mask -
    NOT re-derived connected components of the outcome mask itself. This
    is the fix for the sub-MMU-fragment bug caught during QC (2026-09-20):
    computing components directly on `outcome_mask` would re-fragment a
    single real parcel wherever its pixels split across outcomes."""
    rows = []
    relevant_pids = np.unique(parcel_id[outcome_mask & (parcel_id > 0)])
    for comp_id in relevant_pids:
        comp = parcel_id == comp_id
        area_px = int(comp.sum())
        area_m2 = area_px * pixel_size_m**2
        # Perimeter approximation: boundary pixels = pixels in comp with at
        # least one 4-neighbour outside comp (standard raster-perimeter
        # proxy; exact vector perimeter would need polygonization, deferred
        # as an enhancement - flagged, not silently treated as exact).
        eroded = ndimage.binary_erosion(comp, structure=STRUCT4)
        boundary_px = comp & ~eroded
        perimeter_m = float(boundary_px.sum()) * pixel_size_m
        compactness = (4 * np.pi * area_m2) / (perimeter_m**2) if perimeter_m > 0 else np.nan
        ys, xs = np.where(comp)
        centroid_row, centroid_col = ys.mean(), xs.mean()
        cx, cy = xy(transform, centroid_row, centroid_col)
        rows.append(
            {
                "component_id": comp_id,
                "area_px": area_px,
                "area_m2": area_m2,
                "perimeter_m": perimeter_m,
                "compactness": compactness,
                "centroid_row": centroid_row,
                "centroid_col": centroid_col,
                "centroid_x": cx,
                "centroid_y": cy,
                "pixel_rows": ys,
                "pixel_cols": xs,
            }
        )
    return rows


def nearest_distance_to_mask(target_rows, target_cols, other_mask: np.ndarray, pixel_size_m: float):
    """Euclidean distance transform-based nearest-feature distance from a
    set of (row, col) pixel indices to the nearest True pixel in
    other_mask, excluding the event's own pixels (caller must ensure
    other_mask already has the event's own footprint set False).

    NOTE (data-quality finding, 2026-09-20): in this study window 83-87%
    of pixels are historically agricultural (build_mask.py), and most
    remain cropland outside converted parcels - so nearly every small
    parcel borders cropland at the minimum possible grid distance (one
    pixel, 10 m), making this specific metric saturate at ~10 m for most
    events (confirmed: recovery events had distance_to_agriculture_m with
    ZERO variance, all exactly 10.0 m). Kept for completeness/documentation
    but superseded as the primary connectivity feature by
    agricultural_fraction_within_radius below, which has real variance."""
    dist_map = ndimage.distance_transform_edt(~other_mask) * pixel_size_m
    return dist_map[target_rows, target_cols].min()


def agricultural_fraction_within_radius(centroid_row, centroid_col, ag_mask: np.ndarray, radius_m: float, pixel_size_m: float):
    """Fraction of pixels classified agricultural within `radius_m` of the
    parcel centroid (governing-brief Section X: "percentage of surrounding
    agricultural land" at documented radii, fixed BEFORE looking at
    results - 100/250/500 m, matching the protocol)."""
    radius_px = radius_m / pixel_size_m
    h, w = ag_mask.shape
    r0, r1 = max(0, int(centroid_row - radius_px)), min(h, int(centroid_row + radius_px) + 1)
    c0, c1 = max(0, int(centroid_col - radius_px)), min(w, int(centroid_col + radius_px) + 1)
    window = ag_mask[r0:r1, c0:c1]
    yy, xx = np.mgrid[r0:r1, c0:c1]
    dist = np.sqrt((yy - centroid_row) ** 2 + (xx - centroid_col) ** 2)
    circle = dist <= radius_px
    if circle.sum() == 0:
        return np.nan
    return float(window[circle].mean())


def load_roads_gdf(roads_geojson_path: pathlib.Path, crs):
    import geopandas as gpd

    gdf = gpd.read_file(roads_geojson_path)
    gdf = gdf.set_crs("EPSG:4326").to_crs(crs)
    return gdf


def nearest_road_distance(centroid_xy, roads_gdf) -> float:
    from shapely.geometry import Point

    pt = Point(centroid_xy)
    return float(roads_gdf.distance(pt).min())


def load_ndvi_stack_if_available(window_name: str, years: list[int], target_shape, target_transform):
    """Load whichever Sentinel-2 NDVI composites already exist on disk for
    this window (the STAC pull runs for a long time in the background;
    this function must never assume all years exist). Reprojects each
    available year onto the LULC/label grid (nearest-neighbour is NOT
    appropriate for a continuous variable - bilinear is used instead)
    since the NDVI composite's own window read produced a slightly
    different pixel grid than the LULC pull (different source resolution/
    windowing). Returns (stack, years_actually_loaded)."""
    from rasterio.warp import reproject, Resampling

    available = []
    arrays = []
    for year in years:
        path = DATA_RAW / window_name / "sentinel2_ndvi" / f"{year}.tif"
        if not path.exists():
            continue
        with rasterio.open(path) as src:
            dst = np.full(target_shape, np.nan, dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=dst,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=target_transform,
                dst_crs=src.crs,  # same CRS (UTM 36N) for both - no CRS change needed
                resampling=Resampling.bilinear,
                src_nodata=np.nan,
                dst_nodata=np.nan,
            )
        arrays.append(dst)
        available.append(year)
    if not arrays:
        return None, []
    return np.stack(arrays, axis=0), available


def build_for_window(window_name: str, pixel_size_m: float = 10.0):
    trajectory_label, transform, crs = load_raster(DATA_LABELS / window_name / "trajectory_label.tif")
    first_conv_year, _, _ = load_raster(DATA_LABELS / window_name / "first_conversion_year.tif")
    tier_numeric, _, _ = load_raster(DATA_LABELS / window_name / "label_confidence_tier.tif")
    parcel_id, _, _ = load_raster(DATA_LABELS / window_name / "parcel_id.tif")
    historical_mask, _, _ = load_raster(DATA_PROCESSED / window_name / "historical_agri_mask.tif")
    elevation, dem_transform, _ = load_raster(DATA_RAW / window_name / "dem" / "elevation.tif")
    lulc_2024, _, _ = load_raster(DATA_RAW / window_name / "io_lulc" / "2024.tif")

    tier_map = {2: "A", 1: "B", 0: "C", -1: "N"}

    # "Currently agricultural, not part of any converted event" mask, for
    # the agricultural-connectivity distance feature.
    all_converted = np.isin(trajectory_label, [0, 1])
    current_ag_outside_events = (lulc_2024 == CROP_CLASS) & ~all_converted

    roads_path = DATA_RAW / window_name / "osm_roads" / "roads.geojson"
    roads_gdf = load_roads_gdf(roads_path, crs)

    canals_path = DATA_RAW / window_name / "osm_canals" / "canals.geojson"
    canals_gdf = load_roads_gdf(canals_path, crs) if canals_path.exists() else None
    if canals_gdf is None:
        print(f"[{window_name}] WARNING: no OSM canal data found - distance_to_irrigation_m will be NaN (H4 untestable for this window)")

    builtup_2024 = np.isin(lulc_2024, (7, 8))  # Built + Bare, for built-up-intensity (H3)

    ndvi_baseline_stack, ndvi_years_loaded = load_ndvi_stack_if_available(
        window_name, [2017, 2018, 2019], trajectory_label.shape, transform
    )
    if ndvi_years_loaded:
        print(f"[{window_name}] historical NDVI baseline loaded for years {ndvi_years_loaded}")
    else:
        print(
            f"[{window_name}] WARNING: no Sentinel-2 NDVI composites available yet - "
            "historical vegetation-strength features will be NaN, not silently zero-filled"
        )

    records = []
    for label_value, label_name in ((1, "recovery"), (0, "persistent")):
        mask = trajectory_label == label_value
        comps = parcel_geometry_features(parcel_id, mask, transform, pixel_size_m)
        print(f"[{window_name}] {label_name}: {len(comps)} events")

        for comp in comps:
            rows_px, cols_px = comp["pixel_rows"], comp["pixel_cols"]

            # Historical agricultural strength: fraction of this event's
            # own footprint that qualified as historically agricultural
            # (2017-2019, >=2 years crop) BEFORE conversion.
            hist_agri_frac = float(historical_mask[rows_px, cols_px].mean())

            if ndvi_baseline_stack is not None:
                ndvi_vals = ndvi_baseline_stack[:, rows_px, cols_px]  # (n_years_loaded, n_pixels)
                hist_ndvi_mean = float(np.nanmean(ndvi_vals))
                hist_ndvi_max = float(np.nanmax(ndvi_vals)) if np.any(~np.isnan(ndvi_vals)) else np.nan
                hist_ndvi_std = float(np.nanstd(ndvi_vals))
            else:
                hist_ndvi_mean = hist_ndvi_max = hist_ndvi_std = np.nan

            # Temporal: conversion year + years since conversion (relative
            # to end of record, 2024 - the last year this pipeline has
            # data for).
            conv_years = first_conv_year[rows_px, cols_px]
            conv_year = int(np.round(np.median(conv_years[conv_years > 0]))) if np.any(conv_years > 0) else np.nan
            years_since_conversion = 2024 - conv_year if not np.isnan(conv_year) else np.nan

            # Geometric: already in comp.
            # Environmental: mean elevation, local elevation range as a
            # slope proxy (true slope needs a neighbourhood gradient - this
            # is a coarser proxy pending a proper slope raster).
            elev_vals = sample_raster_at_pixels(elevation, dem_transform, rows_px, cols_px, transform)
            mean_elev = float(np.mean(elev_vals))
            elev_range = float(np.ptp(elev_vals)) if len(elev_vals) > 1 else 0.0

            # GIS/spatial: distance to nearest still-agricultural pixel
            # outside this event, and to nearest OSM road.
            dist_to_agri = nearest_distance_to_mask(rows_px, cols_px, current_ag_outside_events, pixel_size_m)
            ag_frac_radii = {
                radius: agricultural_fraction_within_radius(
                    comp["centroid_row"], comp["centroid_col"], lulc_2024 == CROP_CLASS, radius, pixel_size_m
                )
                for radius in (100, 250, 500)
            }
            try:
                dist_to_road = nearest_road_distance((comp["centroid_x"], comp["centroid_y"]), roads_gdf)
            except Exception as exc:  # noqa: BLE001
                print(f"[{window_name}] road-distance FAILED for component {comp['component_id']}: {exc!r}")
                dist_to_road = np.nan

            # H4: irrigation/water accessibility, via real OSM canal/drain/
            # ditch geometry (governing-brief Section 14.C).
            if canals_gdf is not None and len(canals_gdf) > 0:
                try:
                    dist_to_irrigation = nearest_road_distance((comp["centroid_x"], comp["centroid_y"]), canals_gdf)
                except Exception as exc:  # noqa: BLE001
                    print(f"[{window_name}] canal-distance FAILED for component {comp['component_id']}: {exc!r}")
                    dist_to_irrigation = np.nan
            else:
                dist_to_irrigation = np.nan

            # H3: built-up intensity in the surrounding neighbourhood
            # (governing-brief Section 14.C "urban pressure" / Section V
            # H3 "built-up intensity -> lower recovery potential"), same
            # fixed-radius design as the agricultural-fraction features.
            builtup_frac_radii = {
                radius: agricultural_fraction_within_radius(
                    comp["centroid_row"], comp["centroid_col"], builtup_2024, radius, pixel_size_m
                )
                for radius in (100, 250, 500)
            }

            tier_vals = tier_numeric[rows_px, cols_px]
            vals, freqs = np.unique(tier_vals, return_counts=True)
            mode_tier_code = int(vals[np.argmax(freqs)])

            records.append(
                {
                    "window": window_name,
                    "event_id": f"{window_name}_{label_name}_{comp['component_id']}",
                    "outcome": label_value,
                    "outcome_name": label_name,
                    "label_confidence_tier": tier_map.get(mode_tier_code, "N"),
                    "area_px": comp["area_px"],
                    "area_m2": comp["area_m2"],
                    "perimeter_m": comp["perimeter_m"],
                    "compactness": comp["compactness"],
                    "centroid_x": comp["centroid_x"],
                    "centroid_y": comp["centroid_y"],
                    "historical_agri_fraction": hist_agri_frac,
                    "historical_ndvi_mean": hist_ndvi_mean,
                    "historical_ndvi_max": hist_ndvi_max,
                    "historical_ndvi_std": hist_ndvi_std,
                    "n_ndvi_baseline_years_available": len(ndvi_years_loaded),
                    "conversion_year": conv_year,
                    "years_since_conversion": years_since_conversion,
                    "mean_elevation_m": mean_elev,
                    "elevation_range_m": elev_range,
                    "distance_to_agriculture_m": dist_to_agri,
                    "agri_fraction_r100m": ag_frac_radii[100],
                    "agri_fraction_r250m": ag_frac_radii[250],
                    "agri_fraction_r500m": ag_frac_radii[500],
                    "distance_to_road_m": dist_to_road,
                    "distance_to_irrigation_m": dist_to_irrigation,
                    "builtup_fraction_r100m": builtup_frac_radii[100],
                    "builtup_fraction_r250m": builtup_frac_radii[250],
                    "builtup_fraction_r500m": builtup_frac_radii[500],
                }
            )

    df = pd.DataFrame.from_records(records)
    out_path = OUT_DIR / window_name / "master_dataset.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[{window_name}] master dataset: {len(df)} rows -> {out_path}")
    return df


def main() -> int:
    from utils.study_area import ALL_WINDOW_NAMES  # noqa: E402

    frames = []
    for window_name in ALL_WINDOW_NAMES:
        frames.append(build_for_window(window_name))
    combined = pd.concat(frames, ignore_index=True)
    combined_path = OUT_DIR / "master_dataset_all_windows.csv"
    combined.to_csv(combined_path, index=False)
    print(f"[done] combined: {len(combined)} rows -> {combined_path}")

    tier_summary = combined.groupby(["window", "outcome_name", "label_confidence_tier"]).size()
    print(tier_summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
