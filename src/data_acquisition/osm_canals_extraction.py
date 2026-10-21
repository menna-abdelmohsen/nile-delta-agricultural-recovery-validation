"""Real irrigation/water-accessibility data via OSM waterway tags
(canal, drain, ditch) - the same public Overpass API used for roads,
added to directly test H4 (irrigation/water accessibility relates to
recovery), which the original feature set did not cover (governing-brief
Section 14.C explicitly lists "irrigation accessibility" as a required
GIS feature).

Run directly: `python -m src.data_acquisition.osm_canals_extraction`
"""
from __future__ import annotations

import json
import pathlib
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOWS, StudyWindow  # noqa: E402
from data_acquisition.osm_roads_extraction import overpass_to_geojson  # noqa: E402

OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "ERU-Paper3-AgriculturalRecovery/1.0 (academic research)"}


def fetch_canals(window: StudyWindow) -> dict:
    query = f"""
    [out:json][timeout:90];
    (
      way["waterway"~"canal|drain|ditch"]({window.min_lat},{window.min_lon},{window.max_lat},{window.max_lon});
    );
    out geom;
    """
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.json()


def canals_to_geojson(osm_json: dict) -> dict:
    features = []
    for el in osm_json.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
        features.append(
            {
                "type": "Feature",
                "properties": {"osm_id": el["id"], "waterway": el.get("tags", {}).get("waterway")},
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    for window in ALL_WINDOWS:
        print(f"[osm_canals] fetching {window.name}...")
        try:
            osm_json = fetch_canals(window)
        except Exception as exc:  # noqa: BLE001
            print(f"[osm_canals] {window.name} FAILED: {exc!r}")
            continue
        geojson = canals_to_geojson(osm_json)
        out_dir = OUT_ROOT / window.name.replace(" ", "_") / "osm_canals"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "canals.geojson").write_text(json.dumps(geojson))
        print(f"[osm_canals] {window.name}: {len(geojson['features'])} waterway ways")
    return 0


if __name__ == "__main__":
    sys.exit(main())
