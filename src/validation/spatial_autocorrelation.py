"""Experiment (pre-EXP07): compute Moran's I on the REAL outcome grid to
size the spatial-block CV (protocol Section 9), and explicitly avoid the
wrap-around/edge-cell implementation bug Paper 2's own Limitations section
flagged in its Moran's I computation (it used periodic/wrap-around
neighbour shifts at grid edges instead of excluding them, and did not
re-run the analysis after finding this - this project must not repeat
that mistake).

Computed on the parcel-level outcome (recovery=1 / persistent=0), using
each parcel's centroid, with a proper (non-wrapping) rook-contiguity-style
neighbour definition via a distance-banded weights matrix - appropriate
for point data (parcel centroids), unlike Paper 2's grid-based rook
matrix, since here the analysis unit is an irregularly-spaced parcel
centroid, not a regular raster cell.

Run directly: `python -m src.validation.spatial_autocorrelation`
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

DATA_PROCESSED = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR = pathlib.Path(__file__).resolve().parents[2] / "outputs" / "metrics"


def morans_i(values: np.ndarray, coords: np.ndarray, k_neighbors: int = 8) -> dict:
    """Moran's I with a k-nearest-neighbour weights matrix (no wrap-around
    possible by construction, since neighbours are found by actual
    Euclidean distance in projected coordinates, not by array indexing)."""
    n = len(values)
    tree = cKDTree(coords)
    # k+1 because the nearest neighbour of a point is itself (distance 0).
    dist, idx = tree.query(coords, k=min(k_neighbors + 1, n))

    z = values - values.mean()
    W_sum = 0.0
    numerator = 0.0
    for i in range(n):
        for j_pos in range(1, idx.shape[1]):  # skip self at position 0
            j = idx[i, j_pos]
            w_ij = 1.0  # binary k-NN weight
            numerator += w_ij * z[i] * z[j]
            W_sum += w_ij

    denominator = np.sum(z**2)
    if denominator == 0 or W_sum == 0:
        return {"morans_i": np.nan, "n": n, "k_neighbors": k_neighbors}

    I = (n / W_sum) * (numerator / denominator)

    # Expected value and variance under randomization null (standard
    # formula) for a z-score / p-value.
    expected_I = -1.0 / (n - 1)
    return {"morans_i": float(I), "expected_I_null": expected_I, "n": n, "k_neighbors": k_neighbors}


def permutation_test(values: np.ndarray, coords: np.ndarray, k_neighbors: int, n_perm: int = 999, seed: int = 42):
    rng = np.random.default_rng(seed)
    observed = morans_i(values, coords, k_neighbors)["morans_i"]
    perm_stats = []
    for _ in range(n_perm):
        permuted = rng.permutation(values)
        perm_stats.append(morans_i(permuted, coords, k_neighbors)["morans_i"])
    perm_stats = np.array(perm_stats)
    p_value = float((np.sum(np.abs(perm_stats) >= np.abs(observed)) + 1) / (n_perm + 1))
    return {"observed_I": observed, "p_value_permutation": p_value, "n_permutations": n_perm}


def main() -> int:
    df = pd.read_csv(DATA_PROCESSED / "master_dataset_all_windows.csv")
    results = {}

    for window_name, group in df.groupby("window"):
        coords = group[["centroid_x", "centroid_y"]].to_numpy()
        values = group["outcome"].to_numpy().astype(float)
        mi = morans_i(values, coords, k_neighbors=8)
        perm = permutation_test(values, coords, k_neighbors=8, n_perm=999)
        results[window_name] = {**mi, **perm}
        print(f"[{window_name}] Moran's I = {mi['morans_i']:.4f} (n={mi['n']}), permutation p = {perm['p_value_permutation']:.4f}")

        # Nearest-neighbour distance distribution -> informs a defensible
        # spatial block size (protocol Section 9: "block size to be chosen
        # from an actually-computed Moran's I on the real outcome grid").
        tree = cKDTree(coords)
        dist, _ = tree.query(coords, k=2)
        nn_dist = dist[:, 1]
        results[window_name]["nearest_neighbor_distance_m"] = {
            "median": float(np.median(nn_dist)),
            "p90": float(np.percentile(nn_dist, 90)),
            "max": float(nn_dist.max()),
        }
        print(
            f"[{window_name}] nearest-neighbour parcel distance: median={np.median(nn_dist):.1f} m, "
            f"p90={np.percentile(nn_dist, 90):.1f} m, max={nn_dist.max():.1f} m"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    import json

    out_path = OUT_DIR / "spatial_autocorrelation.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"[done] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
