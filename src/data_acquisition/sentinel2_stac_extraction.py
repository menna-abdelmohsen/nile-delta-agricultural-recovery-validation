"""Real Sentinel-2 growing-season NDVI composites via the public Earth
Search STAC API (element84/AWS `sentinel-cogs` bucket) - no Google Earth
Engine session needed.

Method (documented so it is reproducible, not an ad hoc choice):
  1. STAC-search Sentinel-2 L2A scenes over the study bbox for each
     calendar month in the growing season (March-October), matching
     Paper 2's growing-season definition.
  2. Within each month, keep the single least-cloudy scene
     (eo:cloud_cover minimum) - a documented "monthly best-scene"
     sampling rule, not a cherry-pick of favourable scenes, and bounded
     in cost (<= 8 scenes/year/window rather than every 5-day
     acquisition).
  3. For each kept scene, windowed-read B04, B08, SCL over the study
     bbox directly from the public COGs (`/vsicurl/`, HTTP range
     requests - same technique as public_cog_extraction.py).
  4. Mask using the Scene Classification Layer, keeping only
     {4: vegetation, 5: bare soil, 6: water, 7: unclassified} and
     discarding cloud/shadow/cirrus/snow classes {0,1,2,3,8,9,10,11}.
  5. Compute per-scene NDVI = (B08-B04)/(B08+B04) in float32, then take
     the per-pixel median across the kept, masked scenes for that year
     -> one NDVI composite raster per year per window.

Run directly: `python -m src.data_acquisition.sentinel2_stac_extraction`
"""
from __future__ import annotations

import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import numpy as np
import rasterio
import requests
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOWS, StudyWindow  # noqa: E402

STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"

YEARS = list(range(2017, 2025))
GROWING_SEASON_MONTHS = list(range(3, 11))  # March-October inclusive
MAX_CLOUD_COVER = 60  # scenes above this are never even considered
# SCL class 6 (water) is deliberately EXCLUDED here, unlike the general
# cloud-masking scheme in public_cog_extraction.py's GEE fallback script:
# water pixels have near-zero reflectance in BOTH red and NIR, so
# NDVI's denominator (nir+red) approaches zero and the ratio becomes
# numerically unstable - this produced physically impossible |NDVI| > 1
# values as high as ~54 in an early real run (2018/2019 composites,
# caught during data-quality control 2026-09-20; 2017's composite
# happened to have few enough water pixels in its kept scenes to look
# clean by chance, which is why this was NOT caught until a second year
# was inspected - a reminder to always QC more than one sample). NDVI is
# not a meaningful vegetation index over water anyway, so excluding it is
# correct, not just a numerical workaround.
GOOD_SCL_CLASSES = {4, 5, 7}
NDVI_PHYSICAL_RANGE = (-1.0, 1.0)


def search_month_best_scene(bbox_lonlat, year: int, month: int):
    from calendar import monthrange

    last_day = monthrange(year, month)[1]
    dt_range = f"{year}-{month:02d}-01T00:00:00Z/{year}-{month:02d}-{last_day:02d}T23:59:59Z"
    resp = requests.post(
        STAC_SEARCH_URL,
        json={
            "collections": ["sentinel-2-l2a"],
            "bbox": list(bbox_lonlat),
            "datetime": dt_range,
            "limit": 100,
        },
        timeout=60,
    )
    resp.raise_for_status()
    features = resp.json().get("features", [])
    candidates = [f for f in features if f["properties"].get("eo:cloud_cover", 100) <= MAX_CLOUD_COVER]
    if not candidates:
        return None
    best = min(candidates, key=lambda f: f["properties"]["eo:cloud_cover"])
    return best


_GDAL_HTTP_ENV = rasterio.Env(
    GDAL_HTTP_TIMEOUT=15,
    GDAL_HTTP_CONNECTTIMEOUT=10,
    GDAL_HTTP_MAX_RETRY=0,
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    CPL_VSIL_CURL_USE_HEAD="NO",
)


def read_band_window(url: str, bbox_lonlat):
    """GDAL's /vsicurl/ reads have no timeout by default and can hang
    indefinitely on a stalled connection - this hung for >90s with zero
    output during the Talkha/Sherbin expansion pull (2026-09-21) and had
    to be killed. Wrapping every read in an explicit HTTP timeout/retry
    environment is the fix, not just a workaround: a slow read should
    fail loudly and be retried by the caller, not hang the whole
    pipeline."""
    with _GDAL_HTTP_ENV, rasterio.open(f"/vsicurl/{url}") as src:
        minx, miny, maxx, maxy = transform_bounds("EPSG:4326", src.crs, *bbox_lonlat)
        win = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
        data = src.read(1, window=win, out_dtype="float32", boundless=True, fill_value=0)
        transform = src.window_transform(win)
        crs = src.crs
    return data, transform, crs


def _reflectance_scale_offset(asset: dict) -> tuple[float, float]:
    """Sentinel-2 processing baseline >= 04.00 (from 2022-01-25) adds a
    +1000 DN offset, which earth-search exposes as a raster:bands
    scale/offset pair; older-baseline scenes have offset 0. Reading this
    PER SCENE (rather than assuming one convention for the whole
    2017-2024 record) is required for a physically correct NDVI - see
    research_log.md, this was checked against the actual STAC response
    (2026-09-20) rather than assumed."""
    band_meta = asset.get("raster:bands", [{}])[0]
    return band_meta.get("scale", 0.0001), band_meta.get("offset", 0.0)


def scene_ndvi(feature: dict, bbox_lonlat):
    assets = feature["assets"]
    red_url = assets["red"]["href"]
    nir_url = assets["nir"]["href"]
    scl_url = assets["scl"]["href"]
    red_scale, red_offset = _reflectance_scale_offset(assets["red"])
    nir_scale, nir_offset = _reflectance_scale_offset(assets["nir"])

    red_dn, transform, crs = read_band_window(red_url, bbox_lonlat)
    nir_dn, _, _ = read_band_window(nir_url, bbox_lonlat)
    scl, _, _ = read_band_window(scl_url, bbox_lonlat)

    red = red_dn * red_scale + red_offset
    nir = nir_dn * nir_scale + nir_offset
    # Raw DN of 0 is the documented nodata value for these assets; treat as
    # invalid rather than a (physically impossible) negative-ish reflectance.
    invalid_dn = (red_dn == 0) | (nir_dn == 0)

    # SCL is at 20 m native res while red/nir (this collection's "red"/"nir"
    # assets) are 10 m - shapes can differ by ~2x. Resample SCL to the
    # red/nir grid with nearest-neighbour (categorical) if shapes mismatch.
    if scl.shape != red.shape:
        from scipy.ndimage import zoom

        zy = red.shape[0] / scl.shape[0]
        zx = red.shape[1] / scl.shape[1]
        scl = zoom(scl, (zy, zx), order=0)
        scl = scl[: red.shape[0], : red.shape[1]]

    good = np.isin(scl.astype(np.int16), list(GOOD_SCL_CLASSES)) & ~invalid_dn
    denom = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(denom != 0, (nir - red) / denom, np.nan)
    ndvi = np.where(good, ndvi, np.nan)
    # Physical-range guard: any surviving |NDVI| > 1 indicates a numerically
    # unstable near-zero-denominator pixel (or an atmospheric-correction
    # artifact producing a negative reflectance) that SCL masking alone did
    # not catch - discard rather than silently propagate an impossible value.
    ndvi = np.where(
        (ndvi >= NDVI_PHYSICAL_RANGE[0]) & (ndvi <= NDVI_PHYSICAL_RANGE[1]), ndvi, np.nan
    )
    return ndvi, transform, crs


def build_year_composite(window: StudyWindow, year: int):
    bbox = (window.min_lon, window.min_lat, window.max_lon, window.max_lat)
    scenes_used = []
    ndvi_stack = []
    ref_transform = ref_crs = None

    for month in GROWING_SEASON_MONTHS:
        feature = search_month_best_scene(bbox, year, month)
        if feature is None:
            print(f"[s2] {window.name} {year}-{month:02d}: no usable scene (cloud <= {MAX_CLOUD_COVER}%)")
            continue
        # A hard wall-clock timeout, not just GDAL's own HTTP timeout config
        # (which was found, 2026-09-21, to NOT reliably bound a stalled
        # /vsicurl/ read on this environment/network - one scene hung for
        # multiple minutes regardless of GDAL_HTTP_TIMEOUT). The blocked
        # GDAL call itself cannot be killed from Python (it is a blocking
        # C call), so the worker thread is abandoned, not joined - an
        # acceptable cost in a one-shot acquisition script, and far better
        # than hanging the entire multi-year pull on one bad scene.
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(scene_ndvi, feature, bbox)
            try:
                ndvi, transform, crs = future.result(timeout=20)
            except FutureTimeoutError:
                print(f"[s2] {window.name} {year}-{month:02d}: TIMED OUT reading {feature['id']} (>20s) - skipping")
                continue
            except Exception as exc:  # noqa: BLE001
                print(f"[s2] {window.name} {year}-{month:02d}: FAILED reading {feature['id']}: {exc!r}")
                continue
        if ref_transform is None:
            ref_transform, ref_crs = transform, crs
        if ndvi.shape != ndvi_stack[0].shape if ndvi_stack else False:
            pass  # shapes should match since same bbox/CRS each time; guarded below anyway
        ndvi_stack.append(ndvi)
        scenes_used.append(
            {
                "id": feature["id"],
                "date": feature["properties"]["datetime"],
                "cloud_cover": feature["properties"]["eo:cloud_cover"],
            }
        )
        print(
            f"[s2] {window.name} {year}-{month:02d}: using {feature['id']} "
            f"(cloud={feature['properties']['eo:cloud_cover']:.1f}%)"
        )

    if not ndvi_stack:
        print(f"[s2] {window.name} {year}: NO SCENES AT ALL - skipping year")
        return None

    # Guard against rare shape mismatches across months (different orbit
    # framing) by cropping to the smallest common shape rather than
    # crashing.
    min_h = min(a.shape[0] for a in ndvi_stack)
    min_w = min(a.shape[1] for a in ndvi_stack)
    ndvi_stack = [a[:min_h, :min_w] for a in ndvi_stack]

    composite = np.nanmedian(np.stack(ndvi_stack, axis=0), axis=0).astype(np.float32)

    out_path = OUT_ROOT / window.name.replace(" ", "_") / "sentinel2_ndvi" / f"{year}.tif"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=composite.shape[0],
        width=composite.shape[1],
        count=1,
        dtype=np.float32,
        crs=ref_crs,
        transform=ref_transform,
        nodata=np.nan,
        compress="deflate",
    ) as dst:
        dst.write(composite, 1)

    meta_path = out_path.with_suffix(".scenes.json")
    meta_path.write_text(json.dumps(scenes_used, indent=2))

    valid_frac = np.mean(~np.isnan(composite))
    print(
        f"[s2] {window.name} {year}: composite from {len(scenes_used)} scenes, "
        f"{valid_frac * 100:.1f}% valid pixels -> {out_path}"
    )
    return out_path


def main() -> int:
    for window in ALL_WINDOWS:
        for year in YEARS:
            build_year_composite(window, year)
    return 0


if __name__ == "__main__":
    sys.exit(main())
