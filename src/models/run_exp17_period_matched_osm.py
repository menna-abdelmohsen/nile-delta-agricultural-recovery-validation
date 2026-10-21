"""EXP17 (2026-10-20): replace current-OSM road/canal distances with
period-matched OSM (snapshot 2019-01-01, before every conversion event) and
re-run the identical spatial-CV model comparison.

Step 1 adds `distance_to_road_m_2019` and `distance_to_irrigation_m_2019`
to data/processed/master_dataset_all_windows.csv (original columns kept).
Step 2 re-runs the no-RS and all-features arms with the 2019 columns in
place of the current-OSM columns, same folds/seed/models as EXP03b-10b.
Output: outputs/metrics/exp17_period_matched_osm.json
"""
from __future__ import annotations

import json
import pathlib
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from models.train_baseline_models import (  # noqa: E402
    FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, FEATURE_COLS_RS_ONLY, build_model_factories, run_spatial_cv,
)

MASTER = ROOT / "data" / "processed" / "master_dataset_all_windows.csv"


def nearest(gdf, x, y):
    return float(gdf.distance(Point(x, y)).min()) if len(gdf) else np.nan


def add_columns():
    df = pd.read_csv(MASTER)
    for c in ("distance_to_road_m_2019", "distance_to_irrigation_m_2019"):
        df[c] = np.nan
    for w, g in df.groupby("window"):
        roads = gpd.read_file(ROOT / "data/raw" / w / "osm_roads/roads_2019-01-01.geojson").to_crs("EPSG:32636")
        canals = gpd.read_file(ROOT / "data/raw" / w / "osm_canals/canals_2019-01-01.geojson").to_crs("EPSG:32636")
        for i, r in g.iterrows():
            df.at[i, "distance_to_road_m_2019"] = nearest(roads, r.centroid_x, r.centroid_y)
            df.at[i, "distance_to_irrigation_m_2019"] = nearest(canals, r.centroid_x, r.centroid_y)
    df.to_csv(MASTER, index=False)
    return df


def main():
    df_all = add_columns()
    summ = {}
    for w, g in df_all.groupby("window"):
        summ[w] = {
            "median_road_dist_current_m": round(float(g.distance_to_road_m.median()), 1),
            "median_road_dist_2019_m": round(float(g.distance_to_road_m_2019.median()), 1),
            "median_canal_dist_current_m": round(float(g.distance_to_irrigation_m.median()), 1),
            "median_canal_dist_2019_m": round(float(g.distance_to_irrigation_m_2019.median()), 1),
            "spearman_road_current_vs_2019": round(float(g.distance_to_road_m.corr(g.distance_to_road_m_2019, method="spearman")), 3),
        }
    df = df_all[df_all.label_confidence_tier.isin(["A", "B"])].reset_index(drop=True)
    swap = {"distance_to_road_m": "distance_to_road_m_2019", "distance_to_irrigation_m": "distance_to_irrigation_m_2019"}
    gis19 = [swap.get(c, c) for c in FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL]
    sets = {"no_RS_period_matched_osm": gis19, "all_features_period_matched_osm": gis19 + FEATURE_COLS_RS_ONLY}
    models = build_model_factories(df)
    res = {"feature_distance_comparison": summ}
    for s, cols in sets.items():
        d = df.dropna(subset=cols).reset_index(drop=True)
        res[s] = {"n_used": len(d)}
        for name, f in models.items():
            res[s][name] = run_spatial_cv(d, cols, f"{s}/{name}", f)
    out = ROOT / "outputs" / "metrics" / "exp17_period_matched_osm.json"
    out.write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(summ, indent=2))
    for s in sets:
        for m, r in res[s].items():
            if isinstance(r, dict):
                ci = r["pr_auc_95ci"]
                print(f"{s:34s} {m:20s} PR-AUC={r['pr_auc']:.3f} [{ci['ci_low']:.3f},{ci['ci_high']:.3f}]")


if __name__ == "__main__":
    main()
