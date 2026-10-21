"""Period-matched (historical) OSM roads and canals - added 2026-10-20 to
remove the temporal-leakage risk of using the CURRENT OSM database.

Uses the Overpass API `[date:...]` (attic) setting, which returns the OSM
database exactly as it was at that timestamp. The snapshot date is
2019-01-01T00:00:00Z: it falls inside the 2017-2019 historical baseline
and precedes every parcel's first conversion year (all >= 2020), so no
road or canal mapped after any conversion event can enter a feature.
Same tag filters as `osm_roads_extraction.py` / `osm_canals_extraction.py`.

Outputs: data/raw/<window>/osm_roads/roads_2019-01-01.geojson
         data/raw/<window>/osm_canals/canals_2019-01-01.geojson
Run:     python -m src.data_acquisition.osm_historical_extraction
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from utils.study_area import ALL_WINDOWS  # noqa: E402

SNAPSHOT = "2019-01-01T00:00:00Z"
OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
URL = "https://overpass-api.de/api/interpreter"
UA = "ERU-Paper3-AgriculturalRecovery/1.1 (academic research)"
FILTERS = {"roads": 'way["highway"]', "canals": 'way["waterway"~"canal|drain|ditch"]'}


def fetch(filt, w):
    q = (f'[out:json][timeout:180][date:"{SNAPSHOT}"];'
         f'({filt}({w.min_lat},{w.min_lon},{w.max_lat},{w.max_lon}););out geom;')
    data = urllib.parse.urlencode({"data": q}).encode()
    for attempt in range(20):
        try:
            req = urllib.request.Request(URL, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.load(r)
        except Exception as exc:  # noqa: BLE001
            print(f"  attempt {attempt + 1} failed: {exc!r}", flush=True)
            time.sleep(min(120, 10 * 2 ** attempt))  # exponential backoff (server asks for it)
    raise RuntimeError("Overpass failed")


def to_geojson(js, kind):
    feats = []
    for el in js.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        tags = el.get("tags", {})
        props = {"osm_id": el["id"]}
        props.update({"highway": tags.get("highway"), "name": tags.get("name"), "surface": tags.get("surface")}
                     if kind == "roads" else {"waterway": tags.get("waterway")})
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": "LineString",
                                   "coordinates": [[p["lon"], p["lat"]] for p in el["geometry"]]}})
    return {"type": "FeatureCollection", "snapshot": SNAPSHOT, "features": feats}


def main():
    for w in ALL_WINDOWS:
        wn = w.name.replace(" ", "_")
        for kind, filt in FILTERS.items():
            sub = "osm_roads" if kind == "roads" else "osm_canals"
            out = OUT_ROOT / wn / sub / f"{kind}_2019-01-01.geojson"
            if out.exists():
                print(f"{wn} {kind}: exists"); continue
            gj = to_geojson(fetch(filt, w), kind)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(gj))
            cur = OUT_ROOT / wn / sub / f"{kind}.geojson"
            n_cur = len(json.loads(cur.read_text())["features"]) if cur.exists() else None
            print(f"{wn} {kind}: {len(gj['features'])} ways at {SNAPSHOT} (current extract: {n_cur})", flush=True)
            time.sleep(5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
