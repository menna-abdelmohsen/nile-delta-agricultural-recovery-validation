# Threshold sensitivity vs. visual ground truth (partial, evidence-based)

Per the rescue protocol's Section 13 requirement ("compare candidate recovery
definitions against independent manual ground truth, not model accuracy"), this
note checks the two CONFIRMED TRUE RECOVERY parcels (the only ones in the complete
18-parcel census) against the corrected per-year crop-fraction trajectories
already computed in `outputs/tables/primary_9_parcels_CORRECTED_detail.csv`, to see
whether a stricter simultaneous-majority threshold would have preserved them.

**Caveat, stated plainly**: this check is possible only for the two confirmed true
positives, because per-year corrected trajectories were computed only for the 9
Tier A+B primary parcels (Pilot v1), not for the 9 Tier C parcels (Stratum 1),
where no per-parcel corrected raster trajectory was extracted (only the
final/latest visual state was checked). A complete threshold-vs-truth ROC-style
analysis across all 18 parcels was not performed and is disclosed as unfinished,
not silently assumed.

## The two confirmed true positives against each candidate threshold

| Parcel | 2023 crop fraction | 2024 crop fraction | Passes 50%? | Passes 70%? | Passes 90%? | Passes 100%? |
|---|---|---|---|---|---|---|
| Mit_Salsil_recovery_32 | 0.925 | 1.000 | Yes | Yes | Yes | No |
| Sherbin_recovery_19 | 1.000 | 0.667 | Yes | **No** | No | No |

**Finding**: the ≥50% primary threshold (adopted in Section 3.3, on evidence-based
rather than model-performance grounds per the project's stated discipline) is the
only one of the four candidate thresholds that retains BOTH confirmed genuine
recoveries. Raising the threshold to ≥70% would have already discarded
`Sherbin_recovery_19` — one of only two real recoveries in the entire 332-parcel
dataset — while raising it to ≥90% or 100% would discard it as well and, in the
case of 100%, would additionally have discarded `Mit_Salsil_recovery_32`.

This does NOT mean the ≥50% threshold is "validated" as correct: it retains both
confirmed true positives, but Stratum 1's finding that 8 of 9 Tier C candidates
(all excluded by the automated corroboration tier, not by the simultaneous-majority
threshold itself) are false positives, and Pilot v1's finding that 4 of 9 Tier A+B
candidates are also false positives, together show that no threshold tested in this
project's sensitivity sweep achieves acceptable precision at the parcel level.
Raising the threshold trades away recall (losing genuine recoveries) without a
demonstrated corresponding gain in precision, because the dominant false-positive
mechanism (permanent small structures) is not a function of the crop-fraction
threshold at all — a structure that the classifier reads as "Crops" in one
timestep and "Built" in another will trip a reversal rule at almost any threshold
level, as evidenced by `Mit_Salsil_recovery_26` and `Sherbin_recovery_34` (both
Tier A, both surviving corroboration, both structurally false) in Pilot v1.

**Conclusion for the operational definition (Section 10 of the rescue protocol)**:
threshold tuning alone cannot fix this labeling paradigm's precision problem,
because the primary failure mode is not a threshold-sensitivity issue but a
structural one (misclassification of small permanent features, described in
Section 3.2.1 of the manuscript). This is additional, direct evidence supporting
Outcome C: the fix required is not "pick a better threshold" but "recovery cannot
be reliably operationalized from single-source coarse annual land-cover reversals
alone," which is exactly the paper's revised central contribution.
