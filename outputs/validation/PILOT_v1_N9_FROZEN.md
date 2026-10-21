# PILOT VALIDATION v1 — FROZEN (2026-09-21)

**Status: FROZEN.** This document is the permanent, unmodified record of the first
(pilot) manual visual validation round of this study's primary Tier A+B recovery
candidates. It is superseded in scientific weight (but never deleted or edited) by
any later, larger validation round. All subsequent analysis must cite this
explicitly as "Pilot v1, N=9" and must not silently merge it with later rounds
without clearly distinguishing them in every reported count.

## Scope
- Population checked: all 9 primary Tier A+B "Observed Recovery" parcels in
  `data/processed/master_dataset_all_windows.csv` (label version v2,
  `recovery_label_v2`/`confidence_tier_v2`, EXP02d/EXP02e).
- Method: non-blinded manual Google Earth Web historical-imagery review by the
  research team, with knowledge of each parcel's reported trajectory (used only to
  target which calendar dates to inspect).
- NOT a random or stratified sample of a larger population — this was an
  exhaustive check of the entire primary reported positive class, at the time the
  only definitive claims in the manuscript rested on.

## Frozen result (do not edit numbers below; corrections get a new dated entry, not an edit)

| Parcel | Area (m2) | Tier | Conv. year | Classification | Confidence |
|---|---|---|---|---|---|
| El-Bagalat_recovery_1 | 2200 | A | 2020 | INCONCLUSIVE | Moderate |
| Mit_Salsil_recovery_9 | 2000 | A | 2020 | FALSE POSITIVE | Moderate |
| Mit_Salsil_recovery_26 | 5500 | A | 2020 | FALSE POSITIVE | High |
| Mit_Salsil_recovery_32 | 4000 | B | 2021 | TRUE RECOVERY | Moderate |
| Talkha_recovery_35 | 1800 | B | 2021 | FALSE POSITIVE | Moderate |
| Sherbin_recovery_15 | 1800 | A | 2020 | INCONCLUSIVE | Moderate |
| Sherbin_recovery_19 | 1800 | B | 2021 | TRUE RECOVERY | Moderate |
| Sherbin_recovery_33 | 2400 | B | 2021 | INCONCLUSIVE | Low-moderate |
| Sherbin_recovery_34 | 2900 | B | 2021 | FALSE POSITIVE | High |

TRUE RECOVERY: 2/9 (22.2%), 5,800 m2 (23.8% of area)
FALSE POSITIVE: 4/9 (44.4%), 12,200 m2 (50.0% of area)
INCONCLUSIVE: 3/9 (33.3%), 6,400 m2 (26.2% of area)
Tier A (n=4): 0 confirmed TRUE RECOVERY. Tier B (n=5): 2 confirmed TRUE RECOVERY.

## Known limitations of Pilot v1 (why it is a pilot, not a final result)
1. N=9 is too small to estimate a reliable population-level false-positive rate
   (a rate anywhere from roughly 20% to 70% is statistically compatible with 4/9).
2. Only the automated Tier A+B subset was checked — the study's full candidate pool
   contains 18 total recovery candidates across all confidence tiers (A/B/C) and
   314 persistent-conversion parcels; neither the 9 Tier-C recovery candidates nor
   any persistent-conversion (negative-class) parcel had been independently checked
   as of this freeze.
3. Non-blinded: the reviewer knew each parcel's reported trajectory before
   selecting inspection dates. This could not introduce a false TRUE RECOVERY call
   (dates were chosen to give the labeled trajectory its best chance), so it biases
   toward, not against, confirming the original labels — making the observed 4/9
   false-positive rate, if anything, an underestimate of the true rate under this
   non-blinding direction.
4. Single, non-independent reviewer — no second/blinded reviewer was available in
   this project (disclosed per Section 14 of the governing protocol; not fabricated).

## Use of this pilot going forward
Per the governing protocol (Section 4), this pilot is used to (a) identify concrete
failure mechanisms — permanent-structure misclassification and seasonality
misread as conversion — and (b) inform the design of the expanded validation
sampling protocol in `outputs/validation/expanded_validation_protocol.md`. It is
NOT used, on its own, to make a final Outcome A/B/C determination; that
determination is made after the expanded round completes.
