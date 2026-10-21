"""Spatial block assignment for cross-validation (protocol Section 9),
sized from the REAL nearest-neighbour parcel distances computed in
spatial_autocorrelation.py (median 111-259 m depending on window) rather
than picked arbitrarily or tuned to maximize a later test score.

Uses a simple, auditable grid-block scheme: parcels are assigned to a
block by flooring their (x, y) UTM coordinates to a block_size_m grid
cell - deliberately NOT the wrap-around/periodic neighbour-shift
implementation Paper 2's own Limitations flagged as a bug in ITS Moran's I
computation (irrelevant here anyway, since grid-block assignment by
absolute coordinate has no wrap-around concept), but noted so the
avoidance is explicit and intentional, not accidental.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_BLOCK_SIZE_M = 500.0  # ~2x the larger window's median nearest-neighbour
# parcel distance (259 m, El-Bagalat) and ~4.5x the smaller (111 m, Mit
# Salsil) - chosen to separate most immediate spatial neighbours across
# blocks while keeping enough distinct blocks for k-fold CV given the
# small real sample size (157 Tier A+B parcels pooled). This was fixed
# BEFORE running any model, per protocol Section 9 - it must not be
# re-tuned after seeing CV performance.


def assign_spatial_blocks(df: pd.DataFrame, block_size_m: float = DEFAULT_BLOCK_SIZE_M) -> pd.Series:
    block_col = df["centroid_x"] // block_size_m
    block_row = df["centroid_y"] // block_size_m
    return (block_col.astype(int).astype(str) + "_" + block_row.astype(int).astype(str) + "_" + df["window"])


def spatial_group_kfold_splits(df: pd.DataFrame, n_splits: int, block_size_m: float = DEFAULT_BLOCK_SIZE_M, seed: int = 42):
    """Yields (train_idx, test_idx) with whole spatial blocks assigned
    entirely to one fold (GroupKFold on the block id), so no block's
    parcels are split across train and test."""
    from sklearn.model_selection import GroupKFold

    blocks = assign_spatial_blocks(df, block_size_m)
    n_unique_blocks = blocks.nunique()
    effective_splits = min(n_splits, n_unique_blocks)
    if effective_splits < n_splits:
        print(
            f"[spatial_blocks] WARNING: requested {n_splits} splits but only "
            f"{n_unique_blocks} unique spatial blocks exist - using {effective_splits} instead"
        )
    gkf = GroupKFold(n_splits=effective_splits)
    for train_idx, test_idx in gkf.split(df, groups=blocks):
        yield train_idx, test_idx
