# Spatial-resolution / parcel-size sensitivity analysis (Section 20 of the rescue protocol)

## Question
Does parcel size (relative to the 1,800 m² / 18-pixel minimum mapping unit, MMU)
predict whether a recovery candidate is visually confirmed TRUE RECOVERY, FALSE
POSITIVE, or INCONCLUSIVE? If small parcels near the MMU floor are disproportionately
false positives, this would support excluding them via a larger minimum size.

## Method
All 18 recovery candidates in the complete census were grouped by validation
result and their area (m², and as a multiple of the 1,800 m² MMU) summarized.

| Result | N | Mean area (m²) | Median area (m²) | Min | Max | Std. dev. |
|---|---|---|---|---|---|---|
| TRUE RECOVERY | 2 | 2,900 | 2,900 | 1,800 | 4,000 | 1,556 |
| FALSE POSITIVE | 12 | 3,075 | 2,300 | 1,800 | 7,600 | 1,767 |
| INCONCLUSIVE | 4 | 2,500 | 2,300 | 1,800 | 3,600 | 775 |

## Finding: no size-based separation exists

The mean and median areas of TRUE RECOVERY and FALSE POSITIVE parcels are close
(2,900 vs. 3,075 m² mean; 2,900 vs. 2,300 m² median) and their ranges overlap
almost completely (1,800–4,000 m² vs. 1,800–7,600 m²). Critically, **the smallest
parcel size in the entire dataset (1,800 m², exactly at the MMU floor) appears in
all three outcome categories**: `Sherbin_recovery_19` (TRUE RECOVERY),
`Sherbin_recovery_15` (INCONCLUSIVE), and `Talkha_recovery_35` (FALSE POSITIVE) are
all exactly 1,800 m². No area threshold, however chosen, would cleanly separate
genuine recoveries from false positives in this dataset: raising the minimum
parcel size to exclude the smallest false positives would also exclude the
smallest confirmed genuine recovery (`Sherbin_recovery_19`).

**This is reported as a negative/null finding, not suppressed for being
inconvenient.** It has a direct implication for the paper's structural argument:
the dominant false-positive mechanism (permanent-structure misclassification,
Section 3.2.2) is not primarily a function of how many pixels the parcel spans
— a 5,500 m² parcel (`Mit_Salsil_recovery_26`) and a 2,000 m² parcel
(`Mit_Salsil_recovery_5`) fail for the identical reason (a visually stable
building present throughout the record), while a 7,600 m² parcel
(`Sherbin_recovery_1`) fails for an entirely different reason (a misclassified
historical baseline, unrelated to size). Parcel-size-based filtering is
therefore not a viable mitigation for this study's central problem, reinforcing
that the fix required is evidentiary (independent, multi-source confirmation
before labeling) rather than a simple minimum-mapping-unit adjustment.

## Limitation of this analysis

With only 18 total candidates (2 true positives), this analysis cannot rule out
a real but weak area effect — it can only report that no strong or clean
threshold effect is visible in the available data, which is itself informative
given the question being asked (whether a simple size rule could fix the
labeling pipeline). A larger, expanded dataset (Section 6 of the rescue
protocol) would be needed to test for a weaker area effect with adequate power.
