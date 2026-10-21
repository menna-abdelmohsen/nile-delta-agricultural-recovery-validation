# Stratum 2 results — Persistent-conversion parcels (false-negative check, n=12)

Checking whether each stratified persistent-conversion parcel genuinely never
recovered (CONFIRMED PERSISTENT) or shows a missed genuine recovery
(FALSE NEGATIVE), per `outputs/validation/expanded_validation_protocol.md`.

### 1/12: El-Bagalat_persistent_38 (Tier A)

- Coordinates: 31.142580, 31.626637, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Dense tree/orchard strip near a village, adjacent to an elementary school |
| May 30, 2025 (latest) | Trees mostly cleared; large bare/demolition area with visible foundations and rubble — genuine, ongoing non-agricultural conversion |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: HIGH**
**Reason:** Genuine tree/orchard clearing followed by continued bare/construction land use, consistent with the persistent-conversion label. No evidence of missed recovery.

### 2/12: El-Bagalat_persistent_34 (Tier B)

- Coordinates: 31.184381, 31.658072, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Dense rows of greenhouse/plastic-tunnel agricultural structures beside a canal — an active agricultural facility |
| May 30, 2025 (latest) | Essentially the same greenhouse-tunnel facility, structurally unchanged |

**Result: CONFIRMED PERSISTENT (no missed recovery)**
**Confidence: MODERATE**
**Note (distinct from the false-negative question asked):** No evidence of a genuine open-cropland recovery was found, so this is correctly NOT a false negative. However, the site appears to be a continuously active greenhouse/tunnel agricultural facility across both dates, which raises a separate concern worth flagging for the error taxonomy: solid-roofed greenhouse/tunnel structures are plausibly misclassified as "Built" by the coarse annual land-cover product due to their spectral similarity to rooftops, which could make the ORIGINAL "conversion" label itself spurious (still agricultural production, just under structures) rather than genuine urban/built encroachment. This is a different mechanism from a missed recovery and does not change the CONFIRMED PERSISTENT result for this specific check, but should be documented as an additional identified failure mode.

### 3/12: El-Bagalat_persistent_32 (Tier C)

- Coordinates: 31.195082, 31.616082, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | A fenced farm compound already containing buildings and a greenhouse tunnel, mostly bare/tan yard interior — already developed before the study baseline |
| May 30, 2025 (latest) | Dramatic further development: a large industrial/livestock-shed building (white/tan roof) now dominates the site, beside a canal |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: HIGH**
**Reason:** Genuine, substantial further construction (large new building) at an already-developed farm compound — never reverts toward open cropland. Correctly labeled as persistent conversion.

### 4/12: Mit_Salsil_persistent_100 (Tier A)

- Coordinates: 31.136637, 31.830807, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Target center is at the edge of a village compound bordering a dense dark-green cultivated field |
| May 30, 2025 (latest) | New buildings now occupy the target area (denser construction than 2019) — genuine village expansion into former field |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: MODERATE-HIGH**
**Reason:** Genuine village/building expansion at the field edge, never reverting to cropland.

### 5/12: Mit_Salsil_persistent_98 (Tier B)

- Coordinates: 31.139124, 31.792301, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Target center is within a dense, already-built-up village settlement (buildings, roads, yards) |
| May 30, 2025 (latest) | Same dense village, essentially unchanged, no crop/field visible |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: MODERATE**
**Note:** The parcel is already fully built-up village land well before the claimed conv_year=2023, so the specific "conversion" trigger is unclear (likely a small garden patch or mixed pixel within the village flickering class) — but there is no evidence of any recovery, correctly confirming the persistent-conversion label.

### 6/12: Mit_Salsil_persistent_30 (Tier C)

- Coordinates: 31.204040, 31.780573, conv_year=2021

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Dense, dark-green cultivated field, open field interior (no nearby structure at the exact target) |
| Aug 30, 2020 & Apr 30, 2021 (conv. year) | Same dense green field, essentially unchanged — no visible disturbance |
| May 30, 2025 (latest) | Dark maroon/purple tilled soil (freshly plowed, moist appearance), no built-up/urban signature visible anywhere at the target |

**Result: AMBIGUOUS — NOT a false negative, but the "conversion" label itself looks questionable**
**Confidence: LOW-MODERATE**
**Reason:** No genuine built-up/non-agricultural state is visible at ANY inspected date (2019, 2020, 2021, 2025) — the site cycles between visibly green cultivated field and dark tilled/fallow soil, both of which are normal agricultural states. This does not show a missed recovery (there is no green "recovery" state following a genuine disturbance), but it also does not clearly show the genuine "conversion to non-agricultural use" the persistent-conversion label implies. This suggests the ORIGINAL "conversion" detection may itself be a false positive here — likely triggered by the classifier reading tilled/fallow bare soil as "Built" or "Bare" rather than recognizing it as a normal agricultural fallow stage. Flagged as an additional, distinct failure mode for the error taxonomy (fallow soil misread as conversion), separate from the recovery-side findings.

### 7/12: Sherbin_persistent_5 (Tier A)

- Coordinates: 31.227993, 31.393973, conv_year=2020

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Target center falls directly on a canal + adjacent road (permanent linear infrastructure), with green cultivated fields on both sides |
| May 30, 2025 (latest) | Same canal/road configuration, unchanged; a bare/tan patch visible further from the target on one side |

**Result: CONFIRMED PERSISTENT (technically correct, but reveals a localization/edge-effect concern)**
**Confidence: MODERATE**
**Reason:** A canal/road will never show a "recovery" to cropland by definition, so this is not a false negative. However, the target coordinate landing on permanent linear infrastructure (not a genuine field) both here and in `Sherbin_recovery_33` from Pilot v1 suggests some fraction of both "conversion" and "persistent" labels in this dataset may reflect canal/road-edge mixed pixels rather than genuine parcel-level land-use change — a boundary/edge-effect limitation of the 10 m grid relative to linear infrastructure width, worth disclosing as an additional error-taxonomy item.

### 8/12: Sherbin_persistent_44 (Tier B)

- Coordinates: 31.230445, 31.395229, conv_year=2022

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | A small white-roofed shed structure amid a bare/tan patch, beside a road and green field |
| May 30, 2025 (latest) | The structure has grown substantially into a large blue-roofed shed/warehouse |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: HIGH**
**Reason:** Genuine, substantial building expansion at the site over the observation period — never reverts toward open cropland.

### 9/12: Sherbin_persistent_2 (Tier C)

- Coordinates: 31.251711, 31.376167, conv_year=2020

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Target center at the boundary of a teal/water-colored flooded field and a tree/village cluster near an elementary school |
| Jul 24, 2026 (latest available) | Dramatic surrounding change (the teal field is now dense green cropland), but the exact target center now shows a small school compound (structure, sandy schoolyard) |

**Result: CONFIRMED PERSISTENT (moderate confidence, some localization uncertainty)**
**Confidence: MODERATE**
**Reason:** The target coordinate consistently falls on non-agricultural land (water/pond, then a school compound) distinct from the surrounding fields, which show a genuine and unrelated land-cover change (teal water to green cropland) nearby. No missed recovery is evident AT the target coordinate itself, though the dramatic nearby change underscores how easily a coarse-pixel label can be confounded by adjacent land-use diversity at this specific, visually complex site.

### 10/12: Talkha_persistent_76 (Tier A)

- Coordinates: 31.021920, 31.334332, conv_year=2022

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | A large teal/green plastic-covered greenhouse structure with internal grid divisions, surrounded by tan/sandy ground |
| May 30, 2025 (latest) | Dramatic transformation into a private estate/villa complex: landscaped gardens, a swimming pool, buildings, and driveway paths |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: HIGH**
**Reason:** Genuine, substantial development into a private residential/leisure estate — clearly non-agricultural and never reverting to cropland.

### 11/12: Talkha_persistent_97 (Tier B)

- Coordinates: 31.065149, 31.343317, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Bare/plowed reddish-tan field with a tree/shrub cluster, beside a canal |
| May 30, 2025 (latest) | Same tan, tilled/plowed field (furrow lines visible) with the same tree cluster — no built-up structure visible at either date |

**Result: AMBIGUOUS — same "questionable conversion" pattern as `Mit_Salsil_persistent_30`**
**Confidence: LOW-MODERATE**
**Reason:** No genuine non-agricultural (built/urban) state is visible at either the pre- or post-conversion date — the site appears to be tilled/fallow agricultural land throughout. This is not a false negative (no missed green recovery), but it again suggests the ORIGINAL "conversion" label may itself be a false positive, generated by the classifier reading bare/tilled soil as "Built" rather than a normal fallow agricultural stage — reinforcing this as a real, recurring failure mode (2 of 12 stratum-2 parcels so far) rather than an isolated case.

### 12/12: Talkha_persistent_93 (Tier C)

- Coordinates: 31.067559, 31.414325, conv_year=2023

| Date | Observation |
|---|---|
| Dec 31, 2019 (pre-conversion) | Ambiguous, low-contrast grayish field with diagonal drainage-like lines and a small rectangular structure outline; no clear crop pattern |
| May 30, 2025 (latest) | Dramatic change: a large area of bare, excavated/graded earth with distinctive curved/circular contouring — consistent with substantial construction/earthworks, not agriculture |

**Result: CONFIRMED PERSISTENT (correct negative)**
**Confidence: MODERATE**
**Reason:** The 2025 imagery clearly shows substantial ground disturbance and non-agricultural earthworks/construction, with no crop pattern. This is a genuine, ongoing conversion — no evidence of missed recovery.

---

## Stratum 2 summary (persistent-conversion parcels, stratified, N=12)

| Result | Count |
|---|---|
| CONFIRMED PERSISTENT (correct negative) | 9 |
| AMBIGUOUS — original "conversion" label questionable (fallow/tilled soil, not missed recovery) | 3 (`Mit_Salsil_persistent_30`, `Talkha_persistent_97`, and a milder version of the concern noted for `Sherbin_persistent_5`'s canal/road edge case) |

**Zero false negatives were found** — no persistent-conversion parcel showed a genuine, missed agricultural recovery. This is itself informative: it means the "Persistent Conversion" (negative) class in this dataset is reasonably reliable as a *negative* label (the model is not systematically missing real recoveries by mislabeling them persistent). However, 2–3 of the 12 checked parcels raise a distinct concern: the *"conversion" detection itself* may be a false positive at those sites (tilled/fallow soil misread as built-up), which does not affect the recovery-detection question this validation round targeted, but is a real, additional limitation worth disclosing — it means "n=200 Persistent Conversion" may itself contain some population of parcels that were never genuinely converted to non-agricultural use in the first place. A related edge-effect concern (target coordinates landing on canal/road linear infrastructure rather than field interiors) was also identified in 2 of the 21 newly checked parcels, reinforcing a finding from Pilot v1.
