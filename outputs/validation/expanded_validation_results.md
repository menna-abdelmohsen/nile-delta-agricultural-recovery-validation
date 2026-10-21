# Expanded Independent Validation — Results (in progress)

Frozen sample: `outputs/validation/expanded_validation_FROZEN_sample.csv` (21 parcels:
9 exhaustive Tier-C recovery candidates + 12 stratified persistent-conversion
parcels). Protocol: `outputs/validation/expanded_validation_protocol.md`.

## Stratum 1 — Tier C recovery candidates (exhaustive, n=9)

### 1/9: Mit_Salsil_recovery_5

- Coordinates: 31.196504, 31.815673 (confirmed exact match)
- Area: 2000 m², Tier C, conv_year=2020

| Date | Observation |
|---|---|
| Dec 31, 2019 | Target center is a permanent farm/residential compound: multiple buildings, dirt yard, trees, adjacent to a road; dark (possibly flooded/dense) crop fields on both sides |
| Aug 30, 2020 (conv. year) | Same compound, essentially unchanged, slightly more visible construction/equipment |
| May 30, 2025 (latest) | Same compound, now visibly EXPANDED (additional structures, a pool-like feature) — never reverts to open field |

**Final classification: FALSE POSITIVE**
**Confidence: HIGH**
**Reason:** Same mechanism as `Mit_Salsil_recovery_26`/`Sherbin_recovery_34` from Pilot v1 — a permanent, in this case actively expanding, farm/residential compound misread as cropland by the coarse classifier. Never shows genuine open agricultural land at any inspected date.

### 2/9: Mit_Salsil_recovery_19

- Coordinates: 31.166414, 31.825455 (confirmed exact match)
- Area: 1900 m², Tier C, conv_year=2020

| Date | Observation |
|---|---|
| Dec 31, 2019 | Target center near a road/crossroads amid dense green cultivated fields; a bare/tan disturbed patch and an existing dark-roofed warehouse (with painted lettering) visible nearby but not at the exact center |
| Aug 30, 2020 (conv. year) | A NEW blue-roofed structure has appeared next to the existing warehouse — genuine new construction, absent in 2019 |
| May 30, 2025 (latest) | The 2020 blue-roofed structure is gone, replaced by a different (red/brown-roofed) building cluster in roughly the same footprint — continuous building activity, not a return to open field |

**Final classification: FALSE POSITIVE**
**Confidence: MODERATE-HIGH**
**Reason:** The target location has been under continuous, evolving construction/building activity from 2020 through 2025 (one structure demolished and replaced by another), never reverting to genuine cropland. This is a distinct but related failure mode to the "permanent structure" mechanism: a *changing* structure, not a static one, can still trip the classifier's crop/built assignment back and forth as its spectral signature changes between builds, without any real agricultural recovery occurring.

### 3/9: Mit_Salsil_recovery_22

- Coordinates: 31.159537, 31.768887 (confirmed exact match)
- Area: 3200 m², Tier C, conv_year=2020

| Date | Observation |
|---|---|
| Aug 30, 2020 (conv. year) | Target center falls on a small farm-structure/dirt-yard cluster beside a canal and road; greenhouse tunnels and plowed/bare reddish fields visible nearby but not at the exact center |
| May 30, 2025 (latest) | Same small farm structure and dirt yard persist at the exact center, essentially unchanged; the greenhouse tunnels seen in 2020 nearby are gone, replaced by a furrowed plowed field |

**Final classification: FALSE POSITIVE**
**Confidence: MODERATE**
**Reason:** The exact target coordinate is consistently a small, stable canal-side farm structure with a bare dirt yard across both inspected dates, not open cropland — the same small-structure misclassification mechanism identified repeatedly elsewhere in this study. Some residual localization uncertainty remains given the visually complex, mixed-use surrounding area (greenhouses, plowed fields, dense crop).

### 4/9: Mit_Salsil_recovery_13

- Coordinates: 31.173243, 31.822834 (confirmed exact match)
- Area: 2600 m², Tier C, conv_year=2020

| Date | Observation |
|---|---|
| Jul 30, 2018 (pre-baseline) | Target center is a permanent farm/residential compound with greenhouse-tunnel structures, gardens, and buildings, immediately beside a canal — already present a year before the study baseline begins |
| Aug 30, 2020 (conv. year) | Same compound, essentially unchanged |
| Jun 30, 2024 | Same compound, unchanged |
| May 30, 2025 (latest) | Same compound, unchanged |

**Final classification: FALSE POSITIVE**
**Confidence: HIGH**
**Reason:** Same permanent-structure mechanism — a canal-side farm compound with greenhouse tunnels, stable and unchanged across four independently dated images spanning 2018–2025 (predating the study baseline by a year), never showing genuine open cropland.

### 5/9: Mit_Salsil_recovery_24

- Coordinates: 31.149009, 31.820566 (confirmed exact match)
- Area: 3400 m², Tier C, conv_year=2020

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-baseline) | Target center is a large permanent industrial/warehouse compound (multiple flat-roofed buildings, storage yard), already present before the study baseline |
| Aug 30, 2020 (conv. year) | Same compound, unchanged |
| May 30, 2025 (latest) | Same compound, unchanged |

**Final classification: FALSE POSITIVE**
**Confidence: HIGH**
**Reason:** A large, permanent industrial/warehouse compound, structurally identical across all three inspected dates spanning 2019–2025, never showing open cropland at any point. Same permanent-structure misclassification mechanism as multiple other parcels in this study.

### 6/9: Mit_Salsil_recovery_31

- Coordinates: 31.197396, 31.778355 (confirmed exact match)
- Area: 2000 m², Tier C, conv_year=2021

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Dense, dark-green cultivated field with visible crop rows — genuine agriculture |
| Apr 30, 2021 (conv. year) | Teal/water-like surface and tan/dusty bare ground — genuine disturbance, consistent with conv_year=2021 |
| May 30, 2025 (latest) | A large expanse of bare/textured, non-agricultural-looking ground (no crop pattern), with only a small isolated green rectangular patch (possibly a pond/covered structure) near the road — no genuine return to open cropland |

**Final classification: FALSE POSITIVE**
**Confidence: MODERATE**
**Reason:** Fails the persistence/recovery requirement — the site shows a genuine pre-conversion agricultural baseline and a genuine 2021 disturbance, but the latest available imagery (2025) still shows a large bare, non-agricultural expanse rather than a genuine return to cultivation.

### 7/9: Mit_Salsil_recovery_44

- Coordinates: 31.140957, 31.803623 (confirmed exact match)
- Area: 3600 m², Tier C, conv_year=2021

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Large tan/brown plowed field with fine texture — could be fallow/tilled agricultural soil |
| Apr 30, 2021 (conv. year) | Same tan/plowed field, essentially unchanged, a few light patches possibly debris |
| May 30, 2025 (latest) | Same field, now a uniform gray/purplish tilled surface — no clear green crop cover visible at any inspected date |

**Final classification: INCONCLUSIVE**
**Validation confidence: LOW-MODERATE**
**Reason:** The field shows a consistently bare/tilled, non-green appearance across all three inspected dates (2019, 2021, 2025) with no clear discrete disturbance signature distinguishing the "conversion" year from the baseline, and no clear green recovery signature either. The imagery does not provide clear evidence for or against a genuine conversion-then-recovery cycle at this location — it may simply be a field captured at a fallow/tilled stage of its normal cycle in all three available images.

### 8/9: Sherbin_recovery_1

- Coordinates: 31.256517, 31.392999 (confirmed exact match)
- Area: 7600 m² (the largest Tier C candidate), conv_year=2020

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion, "historically agricultural" per the label) | Large bare/sandy, desert-like open ground with sparse scrub, a surveyed rectangular plot outline, and an adjacent pond/water body — NOT agricultural land |
| Aug 30, 2020 (conv. year) | Same bare/sandy ground, essentially unchanged, survey outline now clearer |
| Jul 24, 2026 (latest available) | Dramatic transformation: dense, well-established GREEN cultivated field with clear crop rows now covers the entire area |

**Final classification: FALSE POSITIVE**
**Confidence: HIGH**
**Reason:** A distinct failure mechanism from the rest of this study's false positives — this is NOT a misclassified permanent structure, but an INCORRECT HISTORICAL-BASELINE classification. The pre-conversion (2017–2019) land here was genuinely bare/desert land, not agricultural, yet the automated historical-agricultural mask (Section 2.4) evidently classified it as "Crops" in enough baseline years to qualify. The dramatic 2019/2020-to-2026 change is real and impressive, but it is **land reclamation (desert converted to new agricultural land)**, not agricultural land recovering after encroachment-driven conversion — a scientifically different phenomenon that this study's labeling pipeline cannot distinguish from genuine recovery, because it only tracks land-cover class transitions, not whether the "historically agricultural" precondition was itself ever true on the ground.

### 9/9: Sherbin_recovery_17

- Coordinates: 31.252850, 31.379411 (confirmed exact match)
- Area: 2000 m², Tier C, conv_year=2021

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Target center is a large permanent building/warehouse structure (beige roof) at a road/canal intersection, surrounded by dark teal (dense crop or flooded) fields |
| Jul 24, 2026 (latest available) | Same building persists (roof now a different shade, possibly repainted/re-roofed), with plowed fields and trees nearby — never shows open cropland |

**Final classification: FALSE POSITIVE**
**Confidence: HIGH**
**Reason:** Same permanent-structure misclassification mechanism as multiple other parcels in this study — a stable building at the exact target coordinate across the full observation record, never genuinely agricultural.

---

## Stratum 1 summary (Tier C recovery candidates, exhaustive, N=9)

| Result | Count | % |
|---|---|---|
| TRUE RECOVERY | 0 | 0% |
| FALSE POSITIVE | 8 | 88.9% |
| INCONCLUSIVE | 1 | 11.1% |

**Zero of the 9 excluded Tier-C recovery candidates were confirmed as genuine recovery** — an even worse rate than the Tier A+B pilot's 2/9. This confirms the automated WorldCover-tiering system has *some* real discriminative value (Tier C is worse than Tier A+B), but the overwhelming Tier-C false-positive rate, combined with the substantial Tier A+B false-positive rate from Pilot v1, shows the underlying reversal-based labeling mechanism itself is unreliable regardless of tier. Failure mechanisms identified in this stratum: permanent farm/residential or industrial structures (6 of 8 false positives), continuous/evolving construction activity (1 of 8), a large-scale desert-to-cropland reclamation project misclassified as "historically agricultural" at baseline (1 of 8, a novel mechanism not seen in Pilot v1), and failure of the persistence requirement (1 of 8).

---

## Stratum 2 — Persistent-conversion parcels, stratified by window x tier (n=12)

(Beginning now.)

