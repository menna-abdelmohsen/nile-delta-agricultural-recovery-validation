# Error taxonomy — synthesized from the complete 18-parcel recovery-candidate census and the 12-parcel persistent-conversion sample

Per the rescue protocol's Section 31 requirement, this taxonomy quantifies failure
mechanisms actually observed in this study's own data (not a generic list), each
tied to specific, named parcels.

## Mechanisms behind the 12 confirmed FALSE POSITIVE recovery candidates (of 18 total)

Mechanisms are mapped onto the land-use categories this study's validation
protocol distinguishes (not a single undifferentiated "structure" bucket), since
these carry different real-world implications for what the "conversion" actually
was.

| Mechanism | Land-use category | Count | Example parcels |
|---|---|---|---|
| Permanent industrial/warehouse compound misclassified as cropland | Industrial/non-agricultural conversion | 1 | `Mit_Salsil_recovery_24` |
| Permanent farm-building/residential compound (with yard/garden) misclassified as cropland | Permanent building | 4 | `Mit_Salsil_recovery_26`, `Mit_Salsil_recovery_5`, `Mit_Salsil_recovery_13`, `Sherbin_recovery_34` |
| Small farm structure near a canal/road edge, moderate localization confidence | Permanent building / road-infrastructure edge effect | 3 | `Mit_Salsil_recovery_22`, `Sherbin_recovery_1` (also flagged separately below for a second, compounding baseline problem), `Sherbin_recovery_17` |
| Continuous/evolving construction activity (a structure is built, then demolished/replaced by a different structure — spectral change trips the reversal rule without ever returning to cropland) | Low-intensity, incrementally expanding development | 1 | `Mit_Salsil_recovery_19` |
| Normal short-cycle crop rotation misread as a discrete conversion-then-recovery event (the same bare/green oscillation is present both before the claimed conversion and after the claimed recovery) | Temporary agricultural disturbance (not encroachment) | 1 | `Talkha_recovery_35` |
| Persistence-requirement failure (a genuine but temporary green signal that does not survive to the latest available date) | Bare/abandoned agricultural land | 1 | `Mit_Salsil_recovery_9` |
| Genuine disturbance but no genuine agricultural return (a large bare/non-agricultural expanse persists at the latest available date) | Bare/abandoned agricultural land | 1 | `Mit_Salsil_recovery_31` |

**Total: 12 (one per false-positive parcel).** `Sherbin_recovery_1` additionally exhibits a second, independent, compounding problem — **incorrect historical-baseline classification**: bare/desert land misclassified as "historically agricultural" at baseline, so a genuine large-scale **land-reclamation** project (new cropland, not recovering cropland) registers as spurious "recovery." This is counted once toward the 12-parcel total (via its small-farm-structure/localization row above) but is discussed as its own distinct phenomenon in the manuscript (Section 3.2.2), because a reclamation project is conceptually the opposite of "agricultural land recovering after encroachment," not a variant of the same failure.

## A related, unresolved ambiguity: flooded rice vs. aquaculture vs. greenhouse

Several parcels' surrounding land cover (not necessarily the exact false-positive
centroid) included a solid, uniform teal/dark-green water-like surface — near
`Mit_Salsil_recovery_31`, `Sherbin_persistent_2`, and in the wider scene around
`Mit_Salsil_recovery_13`/`Sherbin_recovery_17` — that is visually consistent with
at least three distinct real Nile Delta land uses at 10 m resolution: a flooded
rice paddy at early growth stage (genuinely agricultural), an aquaculture/fish
pond (a real, common, and land-use-distinct conversion pathway, particularly near
lake margins, that is neither urban encroachment nor agricultural recovery), or a
solid-roofed plastic greenhouse/tunnel structure. This study's single-date RGB
visual-verification method cannot reliably discriminate between these three
phenomena, and this ambiguity is disclosed as an unresolved limitation rather than
assumed away in any specific direction.

## Mechanisms behind the 4 INCONCLUSIVE recovery candidates

| Mechanism | Count | Example parcels |
|---|---|---|
| No imagery available after a certain date at this specific location (critical persistence-check date unavailable) | 1 | `Sherbin_recovery_15` |
| Cannot confidently localize the small (1,800–3,600 m²) parcel within a larger, visually homogeneous or visually ambiguous surrounding area | 3 | `El-Bagalat_recovery_1`, `Sherbin_recovery_33`, `Mit_Salsil_recovery_44` |

## Mechanisms identified in the persistent-conversion (negative-class) sample (n=12, not exhaustive)

| Mechanism | Count | Example parcels |
|---|---|---|
| Genuine, correctly-labeled persistent conversion (real construction/development, confirmed) | 9 | `El-Bagalat_persistent_38/34/32`, `Mit_Salsil_persistent_100/98`, `Sherbin_persistent_5/44/2`, `Talkha_persistent_76/93` (10 rows collapse to 9 distinct results; see stratum-2 detail file) |
| Original "conversion" label itself questionable — tilled/fallow agricultural soil misread as a built/bare class, not a genuine land-use change | 2 | `Mit_Salsil_persistent_30`, `Talkha_persistent_97` |
| Target coordinate lands on permanent linear infrastructure (canal/road edge) rather than a genuine field interior — a resolution/edge-effect limitation, not a labeling logic error per se | 1 | `Sherbin_persistent_5` |
| Greenhouse/plastic-tunnel agricultural structure plausibly misclassified as "Built" due to solid-roof spectral similarity (flagged as a concern, does not itself invalidate this specific parcel's persistent-conversion label since no recovery was missed) | 1 | `El-Bagalat_persistent_34` |

## Cross-cutting observation

The dominant mechanism across the entire validation campaign — accounting for the
majority of confirmed false positives — is **misclassification of small, spectrally
ambiguous permanent structures** (farm buildings, warehouses, residential compounds),
not seasonality, not resolution alone, and not threshold choice (see
`outputs/validation/threshold_sensitivity_vs_ground_truth.md`). A secondary, smaller
mechanism affecting the negative (persistent-conversion) class is the inverse
problem: bare/tilled agricultural soil misread as a built-up class. Both mechanisms
point to the same underlying root cause: at 10 m resolution, small rural landscape
features (buildings, bare fallow patches, greenhouse tunnels, canal/road edges) do
not have a stable, unambiguous spectral signature in a single annual composite,
and any trajectory-based rule — recovery or otherwise — inherits this instability
whenever it depends on a class assignment flipping between "Crops" and
"Built"/"Bare" from one year to the next.
