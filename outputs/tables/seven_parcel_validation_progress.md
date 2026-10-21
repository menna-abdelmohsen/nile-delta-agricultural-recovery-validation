# Individual visual validation — 7 remaining primary parcels (in progress)

Protocol: Google Earth historical imagery, direct visual inspection at exact parcel
coordinates, three-period check (pre-conversion / conversion / recovery+persistence),
seasonality and false-signal controls applied per user's 18-step protocol
(2026-09-21). Two parcels already done in a prior session segment
(Mit_Salsil_recovery_9 = FALSE POSITIVE, Mit_Salsil_recovery_32 = TRUE RECOVERY) are
recorded in research_log.md and will be merged into the final 9-parcel table.

## Parcel 3 of 7: Talkha_recovery_35

- Coordinates: 31.063919, 31.366854 (confirmed exact match in Google Earth, 0 m offset)
- Area: 1800 m², Tier B, predicted conversion year 2021
- Data trajectory (corrected, simultaneous-majority crop fraction):
  2017=1.0, 2018=1.0, 2019=1.0, 2020=0.389, 2021=0.0, 2022=0.0, 2023=0.778, 2024=0.611

### Dates inspected
| Date | Observation |
|---|---|
| Dec 31, 2019 | Bare/tan field with vehicle-track texture, no crop pattern visible |
| Feb 29, 2020 | Dense green cultivated field, crop rows visible |
| May 30, 2020 | Bare/disturbed brownish soil, no crop pattern |
| May 30, 2021 | Bare/disturbed, dirt tracks crisscrossing, light tan patch (possible debris pile) |
| Jun 30, 2021 | Same bare/disturbed appearance as May 2021 |
| Jul 30, 2021 | Dense green field with visible crop texture (contradicts annual 2021=0.0) |
| Mar 30, 2022 | Tile quality poor / discoloured (likely atmospheric/cloud artifact), not usable |
| May 30, 2022 | Clearly cultivated field, distinct plot/row divisions, green |
| Apr 30, 2023 | Same well-defined cultivated plots, green (matches claimed recovery year) |
| Apr 30, 2024 | Same cultivated plots, dense green (matches claimed persistence) |
| May 30, 2025 (latest available) | Bare/disturbed dirt, vehicle tracks, NO crop pattern — contradicts "persistence" |

### Analysis
The same bare↔green oscillation appears BOTH before the claimed conversion
(Dec 2019 bare → Feb 2020 green → May 2020 bare, all within the "1.0 baseline" period)
AND after the claimed recovery (Apr 2023/2024 green → May 2025 bare again). This
pattern is consistent with normal short-cycle seasonal cropping/fallow rotation
(common for vegetables/berseem in the Nile Delta) rather than a discrete
agricultural→disturbance→recovery event. Two required elements of the TRUE RECOVERY
rule are directly contradicted by direct visual evidence:
1. Pre-conversion "stable agriculture" — baseline period itself already shows the
   same bare/green cycling, undermining the premise of a stable prior state disturbed
   by encroachment.
2. Post-recovery "persistence" — the latest available image (May 2025) shows bare,
   disturbed ground, not agriculture, directly contradicting sustained recovery.

Additional caveat: the parcel (1800 m²) could not be confidently isolated as a
distinct sub-area within the much larger, visually homogeneous surrounding field at
this imagery resolution — a secondary, compounding source of uncertainty.

**Final classification: FALSE POSITIVE**
**Validation confidence: MODERATE**
**Reason:** Seasonality/short-cycle crop rotation is a more plausible explanation for
the observed trajectory than genuine encroachment-driven conversion followed by
genuine recovery; the same oscillation is visible in both the pre-conversion baseline
and after the claimed recovery, and the single latest available image contradicts
persistence.

---

## Parcel 4 of 7: Sherbin_recovery_15

- Coordinates: 31.195031, 31.392174 (confirmed exact match in Google Earth, 0 m offset)
- Area: 1800 m², Tier A, predicted conversion year 2020
- Data trajectory: 2017=1.0, 2018=1.0, 2019=1.0, 2020=0.0, 2021=0.0, 2022=0.444, 2023=1.0, 2024=0.5

### Dates inspected
| Date | Observation |
|---|---|
| Dec 31, 2019 | Dense, uniform reddish-toned crop field east of the road (agricultural). West side of road: sandy/tan ground with sparse dark shrub patches. |
| May 30, 2021 (next available date; no 2020 image exists for this location) | East-of-road area now shows teal/water-like coloring covering what was the crop field — consistent with flooding or conversion to a pond/non-agricultural use. West side: sandy ground with a structure, trucks parked near road. |
| Apr 30, 2023 (= latest available imagery for this location; no 2024/2025 tiles exist here) | East-of-road area is a clean, well-organized dense GREEN cultivated field with clearly visible crop-row/plot structure — matches claimed recovery. |

### Analysis
The sequence is visually clean and directionally consistent with the data:
stable dense crop field (2019) → non-agricultural/water-like surface (2021,
matching the conv_year=2020 dip) → well-organized green cultivated field (2023,
matching the claimed recovery year). No seasonality confound or noise pattern was
observed — the transitions look like genuine, discrete land-use changes rather than
short-cycle oscillation.

However, Google Earth has **no imagery available for this exact location after
April 30, 2023** — the "jump to latest" and "next date" controls are inactive beyond
that tile. This means the claimed 2024 persistence value (0.5) cannot be checked
against any image, and only a **single** post-recovery-period date (Apr 2023) is
available, not the two independent post-recovery dates the decision rule requires
before confirming persistence ("a single green image is insufficient").

**Final classification: INCONCLUSIVE**
**Validation confidence: MODERATE** (evidence is suggestive of genuine recovery, but the
persistence check required by the protocol could not be completed)
**Reason:** Critical post-recovery-period imagery (a second confirmatory date, and any
date at or after the claimed 2024 partial-persistence year) is unavailable for this
location in Google Earth. The available single 2023 image is consistent with recovery,
but per the decision rule a single post-recovery image is insufficient to confirm
TRUE RECOVERY, and there is no imagery available to check for a possible reversion
after April 2023.

---

## Parcel 5 of 7: Sherbin_recovery_19

- Coordinates: 31.232282, 31.327240 (confirmed exact match, 0 m offset)
- Area: 1800 m², Tier B, predicted conversion year 2021
- Data trajectory: 2017=1.0, 2018=1.0, 2019=1.0, 2020=1.0, 2021=0.0, 2022=0.0, 2023=1.0, 2024=0.667

### Dates inspected
| Date | Observation |
|---|---|
| Dec 31, 2019 | Tan/brown plowed field with visible furrow-tillage lines, adjacent to a canal — consistent with dormant/tilled agricultural field |
| Apr 30, 2020 | Tile corrupted (severe overexposure/false-color artifact) — not usable |
| Oct 30, 2021 | Uniform dark purplish-brown bare/wet soil, no crop texture — consistent with conversion/disturbance |
| Apr 30, 2023 | Golden/tan field with clear furrow-row texture (harvested cereal stubble) — agricultural |
| Apr 30, 2024 | Dark green field with distinct plot/row (plastic-mulch-like) pattern — agricultural |
| May 30, 2025 (latest) | Solid, uniform teal-green surface, no visible plant texture — consistent with a flooded rice paddy at early growth stage (common in the Nile Delta in May), though a pond/standing-water interpretation cannot be fully excluded |

### Analysis
A 2020 image exists but is unusable due to a data-quality artifact; the Oct 2021 image
directly confirms bare/disturbed ground, corroborating the conv_year=2021 dip. Three
independent dates after the disturbance (Apr 2023, Apr 2024, May 2025) all show
plausible agricultural cover, satisfying the persistence requirement (more than the
minimum two independent post-recovery dates). The recovery-period images show
different cultivation styles across the three dates (cereal stubble, mulched-row
vegetables, flooded paddy), which is normal Delta crop rotation, not a red flag.

**Final classification: TRUE RECOVERY**
**Validation confidence: MODERATE** (residual uncertainty over whether the 2025 teal
surface is a flooded paddy or standing water, and the 2020 image being unusable means
the exact conversion date within 2020-2021 cannot be pinned down further)
**Reason:** Direct evidence supports agricultural → genuine disturbance (bare soil,
Oct 2021) → genuine, persistent agricultural return, confirmed across three
independent post-disturbance dates spanning 2023-2025, in substantially the same
location.

---

## Parcel 6 of 7: Sherbin_recovery_33

- Coordinates: 31.187069, 31.392816 (confirmed exact match, 0 m offset)
- Area: 2400 m², Tier B, predicted conversion year 2021
- Data trajectory: 2017=1.0, 2018=1.0, 2019=1.0, 2020=0.917, 2021=0.0, 2022=0.0, 2023=0.708, 2024=0.583

### Dates inspected
| Date | Observation |
|---|---|
| Dec 31, 2019 | Target center falls on a narrow tan/sandy strip immediately alongside a paved road, with a dark shrub/tree cluster; a reddish-brown uniform field lies further east |
| May 30, 2021 | Same tan/sandy road-shoulder strip and tree cluster, essentially unchanged from 2019 |
| Apr 30, 2023 | Wider view: dense dark-green crop field west of road; east of road, a beige field with a fine speckled texture (possibly young seedlings on bare soil) |
| May 30, 2024 | Same tan/sandy road-shoulder strip and tree cluster at the exact center point persists; furrowed/plowed tan field and reddish-brown plowed field visible further east |
| May 30, 2025 (latest) | Center point now on a tan, furrow-tilled field extending east — the persistent tree cluster seen in earlier dates is no longer obstructing the view at this exact spot |

### Analysis
Across four of the five inspected dates (2019, 2021, 2024, and partially 2025), the
exact target coordinate consistently falls on or immediately next to a narrow,
apparently semi-permanent sandy/bare road-shoulder strip with a shrub/tree cluster,
rather than showing a clear, unambiguous field interior. This raises a specific,
data-consistent concern: at 10 m resolution, a pixel straddling a road shoulder and
an adjacent cultivated field is prone to mixed-pixel classification instability
(part road/bare-shoulder signal, part neighboring-crop signal), which can produce
exactly this kind of trajectory (high baseline crop fraction, a dip, partial
"recovery") without any real discrete conversion-then-recovery event occurring on
the ground. Because the same ambiguous sandy/shrub feature — not a clearly
cultivated field — occupies the exact target location in three of five dates,
including both before and after the claimed conversion, the parcel could not be
confidently and consistently localized to a genuine field interior.

**Final classification: INCONCLUSIVE**
**Validation confidence: LOW-MODERATE**
**Reason:** Cannot confidently and consistently localize the 2400 m² parcel to a
genuine agricultural field interior rather than a road-shoulder/mixed-pixel edge
location; the same ambiguous sandy/shrub feature persists at the exact target
coordinate across multiple dates spanning both the pre- and post-conversion periods,
making it impossible to reliably distinguish genuine land-use change from
classification noise at a linear-infrastructure edge.

---

## Parcel 7 of 7: Sherbin_recovery_34

- Coordinates: 31.179444, 31.374463 (confirmed exact match, 0 m offset)
- Area: 2900 m², Tier B, predicted conversion year 2021
- Data trajectory: 2017=1.0, 2018=1.0, 2019=1.0, 2020=0.828, 2021=0.0, 2022=0.0, 2023=0.586, 2024=0.828

### Dates inspected
| Date | Observation |
|---|---|
| Dec 31, 2019 | Target center falls on a permanent farm/residential compound: a large flat-roofed warehouse/shed building, a smaller building, a dense cluster of large trees, and small garden plots, bordered by cultivated fields to the east |
| May 30, 2021 | Same compound, same buildings, same footprint — no visible change from 2019 |
| Apr 30, 2023 (wider view) | Confirms the target sits within a genuine, established village/settlement extension: dense rows of small houses, dirt yards, the same large warehouse building, surrounded by agricultural fields but the target location itself is built-up |
| May 30, 2025 (latest) | Identical settlement footprint — warehouse and house rows unchanged, still clearly residential/built-up, not agricultural |

### Analysis
Across all four dates spanning 2019–2025 (i.e., both the entire pre-conversion
baseline period AND the entire claimed conversion/recovery period), the exact target
coordinate shows the same permanent buildings and settlement structures with no
visible change in footprint. There is no date at which this location shows open,
cultivated field — the "agricultural" baseline and the "recovery" state are both
contradicted by direct visual evidence; the location was already a stable
residential/farm-building compound before the claimed baseline period and remains
one today. This is the same failure mode already confirmed for
`Mit_Salsil_recovery_26` in the prior validation round: a permanent small structure
with trees/gardens that the coarse 10 m classifier evidently misreads as cropland in
some years due to spectral ambiguity, producing a spurious "conversion" and
"recovery" signal with no underlying land-use change at all.

**Final classification: FALSE POSITIVE**
**Validation confidence: HIGH**
**Reason:** Direct visual evidence contradicts the required sequence at its very
first step — the site was not genuinely agricultural before the claimed conversion;
it was already a stable, unchanged residential/farm-building compound in the oldest
inspected imagery (2019) and remains structurally identical through the latest
available imagery (2025), with no period showing open cultivated field.

---

# Summary: all 7 remaining primary parcels — final classifications

| # | Parcel | Area (m²) | Tier | Conv. year | Classification | Confidence |
|---|---|---|---|---|---|---|
| 1 | Mit_Salsil_recovery_9 | 2000 | A | 2020 | FALSE POSITIVE | MODERATE |
| 2 | Mit_Salsil_recovery_32 | 4000 | B | 2021 | TRUE RECOVERY | MODERATE |
| 3 | Talkha_recovery_35 | 1800 | B | 2021 | FALSE POSITIVE | MODERATE |
| 4 | Sherbin_recovery_15 | 1800 | A | 2020 | INCONCLUSIVE | MODERATE |
| 5 | Sherbin_recovery_19 | 1800 | B | 2021 | TRUE RECOVERY | MODERATE |
| 6 | Sherbin_recovery_33 | 2400 | B | 2021 | INCONCLUSIVE | LOW-MODERATE |
| 7 | Sherbin_recovery_34 | 2900 | B | 2021 | FALSE POSITIVE | HIGH |

Combined with the 2 parcels already validated in the prior session segment
(`Mit_Salsil_recovery_26` = FALSE POSITIVE, HIGH confidence; `El-Bagalat_recovery_1`
= INCONCLUSIVE), all 9 primary parcels now have a documented classification. Full
9-parcel synthesis (area-weighted totals, Tier A vs Tier B stratification, and the
12-item final output) to follow in the research log and manuscript update.
