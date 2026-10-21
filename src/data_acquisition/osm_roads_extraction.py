"""Real OSM road-network extraction via the public Overpass API - no auth
needed, but the public overpass-api.de instance needs a generous
server-side timeout (90s) and a descriptive User-Agent, or it returns
406/504 under load (confirmed empirically this session - short timeouts
and no User-Agent both failed before this was fixed).

Unlike Paper 2 (which used a single OSM extract frozen at 2017-07-01 and
explicitly flagged zero primary/trunk roads returned for this window as a
limitation), this pull uses the CURRENT OSM database. This is a
deliberate, documented change, not an oversight: Paper 2's own
Limitations section says its single 2017 extract could not be updated for
later years because "subsequent extraction attempts for this window were
unsuccessful." A current-database pull is NOT temporally equivalent to a
frozen 2017 extract (it may include roads built after our T2 cutoffs,
which would be a genuine leakage risk if used naively as a static
predictor for early-period events) - this is flagged for the feature
engineering step to only use road classes/geometries that can be
reasonably assumed stable over the study period (primary/trunk paved
roads), and to treat this as a real limitation in the manuscript, not to
be silently glossed over.

Run directly: `python -m src.data_acquisition.osm_roads_extraction`
"""
from __future__ import annotations

import json
import pathlib
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOWS, StudyWindow  # noqa: E402

OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "ERU-Paper3-AgriculturalRecovery/1.0 (academic research)"}


def fetch_roads(window: StudyWindow) -> dict:
    query = f"""
    [out:json][timeout:90];
    (
      way["highway"]({window.min_lat},{window.min_lon},{window.max_lat},{window.max_lon});
    );
    out geom;
    """
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.json()


def overpass_to_geojson(osm_json: dict) -> dict:
    features = []
    for el in osm_json.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "osm_id": el["id"],
                    "highway": el.get("tags", {}).get("highway"),
                    "name": el.get("tags", {}).get("name"),
                    "surface": el.get("tags", {}).get("surface"),
                },
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    for window in ALL_WINDOWS:
        print(f"[osm_roads] fetching {window.name}...")
        osm_json = fetch_roads(window)
        geojson = overpass_to_geojson(osm_json)

        out_dir = OUT_ROOT / window.name.replace(" ", "_") / "osm_roads"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "roads.geojson").write_text(json.dumps(geojson))

        from collections import Counter

        tag_counts = Counter(f["properties"]["highway"] for f in geojson["features"])
        n_primary_trunk = sum(
            1 for f in geojson["features"] if f["properties"]["highway"] in ("primary", "trunk", "motorway")
        )
        print(
            f"[osm_roads] {window.name}: {len(geojson['features'])} ways, "
            f"highway-class counts={dict(tag_counts)}, primary/trunk/motorway={n_primary_trunk} "
            f"(Paper 2's 2017 extract found 0 for this exact window)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
