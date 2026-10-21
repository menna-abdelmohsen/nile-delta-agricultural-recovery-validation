"""Independent Sentinel-2 trajectory evidence for every labelled parcel
(added 2026-10-20).

Purpose: an objective, reproducible second line of evidence on whether each
parcel (18 recovery candidates + 314 persistent-conversion parcels) really
went cropland -> non-agricultural -> cropland, that does not depend on the
Esri/IO labels used to create the candidates, nor on the visual reviewer.

Method
1. Per-pixel, per-year features from `sentinel2_multiindex_extraction.py`:
   growing-season median NDVI, 90th-percentile NDVI, median NDBI, median MNDWI.
2. A pixel classifier (logistic regression) is trained ONLY on stable
   reference pixels that are NOT part of any labelled parcel: pixels that
   Esri/IO calls cropland in all 8 years AND ESA WorldCover calls cropland in
   both 2020 and 2021 (class 1), versus pixels that Esri/IO calls built-up in
   all 8 years AND WorldCover calls built-up in both years (class 0). Two
   independent products must agree for 10 consecutive product-years, so these
   are high-confidence references. Training pixels are sampled per window and
   year (max 3,000 per class) and evaluated with leave-one-window-out CV.
3. Each parcel-year is AGRICULTURAL if >= 50 % of its valid pixels are
   predicted cropland (the study's own simultaneous-majority rule), WATER if
   >= 50 % have MNDWI > 0, otherwise NON-AGRICULTURAL; UNKNOWN if < 50 % of the
   parcel's pixels are valid that year.
4. Trajectory verdict relative to the parcel's Esri/IO first-conversion year c
   (rules fixed before comparing with the visual census):
   - NOT_AG_BEFORE      : fewer than half of the pre-c years are agricultural
   - NO_CONVERSION_SEEN : agricultural in every known year 2017-2025
   - RECOVERY           : agricultural before c, a non-agricultural year at or
                          after c, then agricultural in >= 2 consecutive years
                          that run to the end of the record (2025)
   - PERSISTENT_NONAG   : non-agricultural at/after c and not RECOVERY
   - UNCLEAR            : anything else (e.g. too many unknown years)
Outputs: outputs/validation/s2_trajectory_evidence_parcels.csv,
         outputs/validation/s2_trajectory_evidence_summary.json
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling, reproject
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW, LAB = ROOT / "data" / "raw", ROOT / "data" / "labels"
OUT = ROOT / "outputs" / "validation"
WINDOWS = ["El-Bagalat", "Mit_Salsil", "Talkha", "Sherbin"]
YEARS = list(range(2017, 2026))
LULC_YEARS = list(range(2017, 2025))
FEATS = ["ndvi_med", "ndvi_p90", "ndbi_med", "mndwi_med"]
RNG = np.random.default_rng(42)


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1), s.transform, s.crs


def worldcover_on_grid(w, year, shape, tr, crs):
    with rasterio.open(RAW / w / "esa_worldcover" / f"{year}.tif") as s:
        out = np.zeros(shape, dtype=np.uint8)
        reproject(s.read(1), out, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
    return out


def load_window(w):
    pid, tr, crs = rd(LAB / w / "parcel_id.tif")
    lulc = np.stack([rd(RAW / w / "io_lulc" / f"{y}.tif")[0] for y in LULC_YEARS])
    wc = np.stack([worldcover_on_grid(w, y, pid.shape, tr, crs) for y in (2020, 2021)])
    feats = {}
    for y in YEARS:
        feats[y] = np.stack([rd(RAW / w / "sentinel2_indices" / f"{y}_{f}.tif")[0][: pid.shape[0], : pid.shape[1]]
                             for f in FEATS], axis=-1)
    stable_crop = (lulc == 5).all(0) & (wc == 40).all(0) & (pid == 0)
    stable_built = (lulc == 7).all(0) & (wc == 50).all(0) & (pid == 0)
    return pid, feats, stable_crop, stable_built


def main():
    data = {w: load_window(w) for w in WINDOWS}
    # ---- reference training set
    X, Y, G = [], [], []
    for w, (pid, feats, sc, sb) in data.items():
        for y in YEARS:
            f = feats[y]
            for cls, m in ((1, sc), (0, sb)):
                idx = np.flatnonzero(m.ravel())
                v = f.reshape(-1, len(FEATS))[idx]
                v = v[~np.isnan(v).any(1)]
                if len(v) > 3000:
                    v = v[RNG.choice(len(v), 3000, replace=False)]
                X.append(v); Y.append(np.full(len(v), cls)); G.append(np.full(len(v), w, dtype=object))
    X, Y, G = np.vstack(X), np.concatenate(Y), np.concatenate(G)
    cv = {}
    for w in WINDOWS:
        tr_ = G != w
        clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X[tr_], Y[tr_])
        cv[w] = float(balanced_accuracy_score(Y[~tr_], clf.predict(X[~tr_])))
    clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X, Y)
    print("reference pixels:", {int(k): int((Y == k).sum()) for k in (0, 1)}, "LOWO balanced acc:", cv)

    # ---- parcel-year states
    master = pd.read_csv(ROOT / "data" / "processed" / "master_dataset_all_windows.csv")
    rows = []
    for _, r in master.iterrows():
        w = r.window
        pid, feats, _, _ = data[w]
        n = int(r.event_id.rsplit("_", 1)[1])
        m = pid == n
        states, agfr = {}, {}
        for y in YEARS:
            v = feats[y][m]
            ok = ~np.isnan(v).any(1)
            if ok.mean() < 0.5:
                states[y] = "U"; agfr[y] = np.nan; continue
            v = v[ok]
            p_ag = clf.predict(v).mean()
            water = (v[:, 3] > 0).mean()
            agfr[y] = float(p_ag)
            states[y] = "A" if p_ag >= 0.5 else ("W" if water >= 0.5 else "N")
        c = int(r.conversion_year)
        pre = [states[y] for y in YEARS if y < c and states[y] != "U"]
        post = [(y, states[y]) for y in YEARS if y >= c]
        known = [s for s in states.values() if s != "U"]
        seq = [states[y] for y in YEARS]
        # trailing agricultural run to end of record
        tail = 0
        for s in reversed(seq):
            if s == "A":
                tail += 1
            else:
                break
        nonag_post = [y for y, s in post if s in ("N", "W")]
        if pre and sum(s == "A" for s in pre) < len(pre) / 2:
            v_ = "NOT_AG_BEFORE"
        elif known and all(s == "A" for s in known) and len(known) >= 6:
            v_ = "NO_CONVERSION_SEEN"
        elif nonag_post and tail >= 2 and YEARS[-tail] > min(nonag_post):
            v_ = "RECOVERY"
        elif nonag_post:
            v_ = "PERSISTENT_NONAG"
        else:
            v_ = "UNCLEAR"
        rows.append({"event_id": r.event_id, "window": w, "outcome_name": r.outcome_name,
                     "tier": r.label_confidence_tier, "conversion_year": c, "area_m2": r.area_m2,
                     "s2_states_2017_2025": "".join(seq), "water_years": sum(s == "W" for s in seq),
                     "s2_verdict": v_, **{f"ag_frac_{y}": agfr[y] for y in YEARS}})
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "s2_trajectory_evidence_parcels.csv", index=False)
    summ = {"reference_pixels": {"cropland": int((Y == 1).sum()), "built": int((Y == 0).sum())},
            "leave_one_window_out_balanced_accuracy": cv,
            "classifier_coefficients": dict(zip(FEATS, clf.coef_[0].round(3).tolist())),
            "verdicts_by_label": df.groupby(["outcome_name", "s2_verdict"]).size().unstack(fill_value=0).to_dict("index")}
    (OUT / "s2_trajectory_evidence_summary.json").write_text(json.dumps(summ, indent=2))
    print(json.dumps(summ, indent=2))
    return df


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)
