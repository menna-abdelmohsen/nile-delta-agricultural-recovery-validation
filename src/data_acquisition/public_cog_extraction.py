"""Real data acquisition via public, unauthenticated Cloud-Optimized GeoTIFFs
(no Google Earth Engine account/session needed).

Verified public, license-clear sources (checked 2026-09-20, see
research_log.md for the exact HTTP checks that confirmed each one):

  - Esri / Impact Observatory 10 m Annual LULC (2017-2024), CC-BY-4.0,
    served as per-UTM-zone "supercell" COGs by Impact Observatory's own
    STAC API + S3 bucket (`io-10m-annual-lulc`, us-west-2). This is the
    SAME dataset Paper 2 used as its outcome-label source.
  - ESA WorldCover v100 (2020) / v200 (2021), CC-BY-4.0, 3x3-degree tiled
    COGs on the `esa-worldcover` S3 bucket (eu-central-1).
  - Copernicus DEM GLO-30, public S3 bucket `copernicus-dem-30m`.

All three are read with `rasterio` via GDAL's `/vsicurl/` virtual file
system, which performs HTTP range requests against the COG's internal
tiling/overview structure - only the study-window's pixels are actually
downloaded, not the full (multi-GB, whole-UTM-zone or continental) file.

This module intentionally does NOT touch Sentinel-2 - see
sentinel2_stac_extraction.py for that (it needs scene search + cloud
masking + compositing, a materially different, heavier pipeline).
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from rasterio.enums import Resampling

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOWS, StudyWindow  # noqa: E402

OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"

IO_LULC_YEARS = list(range(2017, 2025))  # 2017-2024, full available record
IO_LULC_URL_TMPL = (
    "/vsicurl/https://s3.us-west-2.amazonaws.com/io-10m-annual-lulc/{utm_supercell}_{year}.tif"
)
# El-Bagalat and Mit Salsil both fall in UTM zone 36, MGRS latitude band R
# (confirmed via the Impact Observatory STAC API bbox query, 2026-09-20:
# querying bbox=31.582,31.125,31.673,31.205 returned items "36R-2017"..
# "36R-2024" and no other supercell id).
UTM_SUPERCELL = "36R"

WORLDCOVER_TILE = "N30E030"  # confirmed to cover both windows (30-33E, 30-33N)
WORLDCOVER_URL_TMPL = (
    "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "{version}/{year}/map/ESA_WorldCover_10m_{year}_{version}_{tile}_Map.tif"
)
WORLDCOVER_VERSIONS = {2020: "v100", 2021: "v200"}

# Copernicus DEM GLO-30 tile naming: Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM
# El-Bagalat/Mit Salsil both fall within lat 31, lon 31 AND lon 31->32 band
# (Mit Salsil's reconstructed box may cross into E031/E032 - both tiles are
# fetched and mosaicked defensively).
DEM_URL_TMPL = (
    "/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM/"
    "Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM.tif"
)


def _read_window_lonlat(url: str, window_bbox_lonlat: tuple[float, float, float, float]):
    with rasterio.open(url) as src:
        minx, miny, maxx, maxy = transform_bounds(
            "EPSG:4326", src.crs, *window_bbox_lonlat
        )
        win = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
        data = src.read(1, window=win)
        transform = src.window_transform(win)
        crs = src.crs
        nodata = src.nodata
    return data, transform, crs, nodata


def _write_geotiff(path: pathlib.Path, data: np.ndarray, transform, crs, nodata=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        dst.write(data, 1)


def fetch_io_lulc(window: StudyWindow) -> dict[int, pathlib.Path]:
    bbox = (window.min_lon, window.min_lat, window.max_lon, window.max_lat)
    out = {}
    for year in IO_LULC_YEARS:
        url = IO_LULC_URL_TMPL.format(utm_supercell=UTM_SUPERCELL, year=year)
        try:
            data, transform, crs, nodata = _read_window_lonlat(url, bbox)
        except Exception as exc:  # noqa: BLE001
            print(f"[io_lulc] FAILED {window.name} {year}: {exc!r}")
            continue
        out_path = OUT_ROOT / window.name.replace(" ", "_") / "io_lulc" / f"{year}.tif"
        _write_geotiff(out_path, data, transform, crs, nodata)
        vals, counts = np.unique(data, return_counts=True)
        print(
            f"[io_lulc] {window.name} {year}: shape={data.shape} "
            f"classes={dict(zip(vals.tolist(), counts.tolist()))} -> {out_path}"
        )
        out[year] = out_path
    return out


def fetch_worldcover(window: StudyWindow) -> dict[int, pathlib.Path]:
    bbox = (window.min_lon, window.min_lat, window.max_lon, window.max_lat)
    out = {}
    for year, version in WORLDCOVER_VERSIONS.items():
        url = WORLDCOVER_URL_TMPL.format(version=version, year=year, tile=WORLDCOVER_TILE)
        try:
            data, transform, crs, nodata = _read_window_lonlat(url, bbox)
        except Exception as exc:  # noqa: BLE001
            print(f"[worldcover] FAILED {window.name} {year}: {exc!r}")
            continue
        out_path = OUT_ROOT / window.name.replace(" ", "_") / "esa_worldcover" / f"{year}.tif"
        _write_geotiff(out_path, data, transform, crs, nodata)
        vals, counts = np.unique(data, return_counts=True)
        print(
            f"[worldcover] {window.name} {year}: shape={data.shape} "
            f"classes={dict(zip(vals.tolist(), counts.tolist()))} -> {out_path}"
        )
        out[year] = out_path
    return out


def fetch_dem(window: StudyWindow) -> pathlib.Path | None:
    import math

    bbox = (window.min_lon, window.min_lat, window.max_lon, window.max_lat)
    lat_tiles = sorted({math.floor(window.min_lat), math.floor(window.max_lat)})
    lon_tiles = sorted({math.floor(window.min_lon), math.floor(window.max_lon)})

    arrays = []
    ref_transform = ref_crs = ref_nodata = None
    for lat in lat_tiles:
        for lon in lon_tiles:
            url = DEM_URL_TMPL.format(lat=lat, lon=lon)
            try:
                data, transform, crs, nodata = _read_window_lonlat(url, bbox)
            except Exception as exc:  # noqa: BLE001
                print(f"[dem] tile N{lat:02d}E{lon:03d} not usable for {window.name}: {exc!r}")
                continue
            if data.size == 0:
                continue
            arrays.append(data)
            ref_transform, ref_crs, ref_nodata = transform, crs, nodata

    if not arrays:
        print(f"[dem] FAILED {window.name}: no DEM tile covered this window")
        return None

    # Windows already clip to the window bbox per-tile; if the window spans
    # two tiles, prefer the tile with more valid (non-nodata) pixels rather
    # than naively overwriting - flagged here as a simplification to revisit
    # if Mit Salsil's reconstructed box turns out to straddle a DEM tile edge.
    best = max(arrays, key=lambda a: np.count_nonzero(a != ref_nodata) if ref_nodata is not None else a.size)
    out_path = OUT_ROOT / window.name.replace(" ", "_") / "dem" / "elevation.tif"
    _write_geotiff(out_path, best, ref_transform, ref_crs, ref_nodata)
    print(f"[dem] {window.name}: shape={best.shape} -> {out_path}")
    return out_path


def main() -> int:
    for window in ALL_WINDOWS:
        print(f"=== {window.name} ===")
        fetch_io_lulc(window)
        fetch_worldcover(window)
        fetch_dem(window)
    return 0


if __name__ == "__main__":
    sys.exit(main())
