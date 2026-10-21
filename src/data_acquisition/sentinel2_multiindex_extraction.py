"""Sentinel-2 multi-index annual composites (NDVI, NDBI, MNDWI) for every
study window, 2017-2025 - added 2026-10-20 to (a) close the Talkha/Sherbin
Sentinel-2 gap and (b) give every parcel an objective, imagery-derived
land-cover trajectory that is independent of the Esri/IO labels and of the
visual reviewer.

Scene selection, cloud masking and NDVI computation follow
`sentinel2_stac_extraction.py` exactly (monthly least-cloudy L2A scene,
March-October, cloud <= 60 %, SCL classes {4,5,7}, per-scene scale/offset),
so the NDVI composite written to `sentinel2_ndvi/<year>.tif` is the same
product the original script produces. Additional per-year outputs in
`sentinel2_indices/`:
  ndvi_med, ndvi_p90   median / 90th percentile NDVI across kept scenes
  ndbi_med             (SWIR1 - NIR) / (SWIR1 + NIR)  - built-up / bare
  mndwi_med            (Green - SWIR1) / (Green + SWIR1) - open water
For MNDWI, water pixels (SCL 6) are KEPT (water is what it detects); for
NDVI/NDBI they stay excluded, as in the original script. All bands are
read on the 10 m red/nir grid (20 m SWIR1/SCL resampled nearest-neighbour).

Run:  python -m src.data_acquisition.sentinel2_multiindex_extraction [WINDOW ...]
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOWS  # noqa: E402
from data_acquisition.sentinel2_stac_extraction import (  # noqa: E402
    GOOD_SCL_CLASSES, GROWING_SEASON_MONTHS, MAX_CLOUD_COVER,
    _reflectance_scale_offset, search_month_best_scene,
)

OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
YEARS = list(range(2017, 2026))
WATER_OK = set(GOOD_SCL_CLASSES) | {6}
ENV = dict(GDAL_HTTP_TIMEOUT=30, GDAL_HTTP_CONNECTTIMEOUT=15, GDAL_HTTP_MAX_RETRY=3,
           GDAL_HTTP_RETRY_DELAY=2, CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
           GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_USE_HEAD="NO")


def _read(url, bbox, shape=None, resampling=Resampling.nearest):
    with rasterio.Env(**ENV), rasterio.open(f"/vsicurl/{url}") as src:
        b = transform_bounds("EPSG:4326", src.crs, *bbox)
        win = from_bounds(*b, transform=src.transform)
        kw = dict(window=win, boundless=True, fill_value=0, out_dtype="float32")
        if shape is not None:
            kw.update(out_shape=shape, resampling=resampling)
        data = src.read(1, **kw)
        return data, src.window_transform(win), src.crs


def scene_indices(feature, bbox):
    a = feature["assets"]
    red_dn, tr, crs = _read(a["red"]["href"], bbox)
    shp = red_dn.shape
    nir_dn, _, _ = _read(a["nir"]["href"], bbox, shp)
    grn_dn, _, _ = _read(a["green"]["href"], bbox, shp)
    sw_dn, _, _ = _read(a["swir16"]["href"], bbox, shp)
    scl, _, _ = _read(a["scl"]["href"], bbox, shp)
    refl = {}
    for k, dn in (("red", red_dn), ("nir", nir_dn), ("green", grn_dn), ("swir16", sw_dn)):
        s, o = _reflectance_scale_offset(a[k])
        refl[k] = dn * s + o
    invalid = (red_dn == 0) | (nir_dn == 0) | (grn_dn == 0) | (sw_dn == 0)
    scl = scl.astype(np.int16)
    land = np.isin(scl, list(GOOD_SCL_CLASSES)) & ~invalid
    wet = np.isin(scl, list(WATER_OK)) & ~invalid

    def nd(x, y, mask):
        with np.errstate(divide="ignore", invalid="ignore"):
            v = np.where((x + y) != 0, (x - y) / (x + y), np.nan)
        v = np.where(mask & (v >= -1) & (v <= 1), v, np.nan)
        return v.astype(np.float32)

    return (nd(refl["nir"], refl["red"], land), nd(refl["swir16"], refl["nir"], land),
            nd(refl["green"], refl["swir16"], wet), tr, crs)


def _write(path, arr, tr, crs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype="float32", crs=crs, transform=tr, nodata=np.nan, compress="deflate") as d:
        d.write(arr.astype(np.float32), 1)


def build(window, year, write_ndvi_product: bool):
    bbox = (window.min_lon, window.min_lat, window.max_lon, window.max_lat)
    wname = window.name.replace(" ", "_")
    out_dir = OUT_ROOT / wname / "sentinel2_indices"
    if (out_dir / f"{year}_ndvi_med.tif").exists():
        print(f"[s2x] {wname} {year}: exists, skip", flush=True)
        return
    stacks = {"ndvi": [], "ndbi": [], "mndwi": []}
    used, tr0, crs0 = [], None, None
    for month in GROWING_SEASON_MONTHS:
        f = None
        for attempt in range(3):
            try:
                f = search_month_best_scene(bbox, year, month)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"[s2x] {wname} {year}-{month:02d}: search error {exc!r}, retry", flush=True)
                time.sleep(5)
        if f is None:
            continue
        res = None
        for attempt in range(2):
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(scene_indices, f, bbox)
                try:
                    res = fut.result(timeout=120)
                    break
                except FutureTimeoutError:
                    print(f"[s2x] {wname} {year}-{month:02d}: timeout {f['id']}", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"[s2x] {wname} {year}-{month:02d}: fail {f['id']} {exc!r}", flush=True)
        if res is None:
            continue
        ndvi, ndbi, mndwi, tr, crs = res
        if tr0 is None:
            tr0, crs0 = tr, crs
        stacks["ndvi"].append(ndvi); stacks["ndbi"].append(ndbi); stacks["mndwi"].append(mndwi)
        used.append({"id": f["id"], "date": f["properties"]["datetime"],
                     "cloud_cover": f["properties"]["eo:cloud_cover"]})
        print(f"[s2x] {wname} {year}-{month:02d}: {f['id']} cloud={f['properties']['eo:cloud_cover']:.1f}", flush=True)
    if not used:
        print(f"[s2x] {wname} {year}: NO SCENES", flush=True)
        return
    h = min(a.shape[0] for a in stacks["ndvi"]); w = min(a.shape[1] for a in stacks["ndvi"])
    st = {k: np.stack([a[:h, :w] for a in v]) for k, v in stacks.items()}
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        outs = {"ndvi_med": np.nanmedian(st["ndvi"], 0), "ndvi_p90": np.nanpercentile(st["ndvi"], 90, 0),
                "ndbi_med": np.nanmedian(st["ndbi"], 0), "mndwi_med": np.nanmedian(st["mndwi"], 0)}
    for k, v in outs.items():
        _write(out_dir / f"{year}_{k}.tif", v, tr0, crs0)
    (out_dir / f"{year}.scenes.json").write_text(json.dumps(used, indent=2))
    if write_ndvi_product:
        p = OUT_ROOT / wname / "sentinel2_ndvi" / f"{year}.tif"
        if not p.exists():
            _write(p, outs["ndvi_med"], tr0, crs0)
            p.with_suffix(".scenes.json").write_text(json.dumps(used, indent=2))
    print(f"[s2x] {wname} {year}: {len(used)} scenes, valid={np.mean(~np.isnan(outs['ndvi_med']))*100:.1f}%", flush=True)


def main(argv):
    names = set(argv) or {w.name for w in ALL_WINDOWS}
    for w in ALL_WINDOWS:
        if w.name not in names and w.name.replace(" ", "_") not in names:
            continue
        for y in YEARS:
            # the NDVI model feature uses the 2017-2019 baseline years only;
            # write it for windows that have no original product yet
            build(w, y, write_ndvi_product=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
