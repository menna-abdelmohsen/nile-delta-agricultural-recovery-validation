# Expanded Independent Validation Protocol — FROZEN BEFORE INSPECTION (2026-09-21)

## Purpose
Address Pilot v1's core limitation (N=9, positive-class-only, automated-tier-only)
by (a) exhausting the recovery-candidate population outside the automated Tier A+B
cutoff, and (b) sampling the negative (persistent-conversion) class across window
and tier to check the false-negative rate and general reliability of the "never
recovered" label — not just re-checking the positive class.

## Sampling frame
Full `data/processed/master_dataset_all_windows.csv` (N=332: 18 recovery
candidates across Tiers A/B/C, 314 persistent-conversion parcels across Tiers
A/B/C, 4 windows).

## Strata (frozen; sample size fixed before any parcel was opened in Google Earth)

**Stratum 1 — Recovery candidates, Tier C (exhaustive, n=9).** All recovery
candidates that the automated WorldCover-agreement tiering placed in Tier C
(neither year corroborated, or not checkable) were excluded from Pilot v1 and
from the primary modeling dataset entirely. Checking all 9 answers two questions
at once: (a) does the automated tiering correctly discard genuine false positives
by relegating them to Tier C, or (b) does it also discard genuine recoveries that
a stricter automated rule wrongly penalizes for a WorldCover-agreement failure
unrelated to the ground truth?

**Stratum 2 — Persistent-conversion parcels, stratified by window x tier
(n=12, 1 per cell, fixed random seed=42).** 4 windows x 3 tiers = 12 cells, one
parcel drawn per cell via `pandas.DataFrame.sample(random_state=42)` — a
reproducible, auditable draw, not a hand-picked selection. This stratum checks
whether the "Persistent Conversion" (never-reversed) label is itself reliable, and
specifically probes for false negatives: a persistent-conversion parcel that
visual inspection shows DID genuinely recover but was missed by the automated
reversal rule (e.g., because the reversal happened just outside the observation
window, or a real green recovery period fell entirely within a single Esri/IO
annual composite and never satisfied the simultaneous-majority two-year
requirement).

**Total new parcels: 21.** Combined with Pilot v1's 9, this is a 30-parcel complete
validation campaign — the largest achievable within this project's manual,
single-reviewer, browser-driven verification method (Section 14's blinded
second-reviewer step was not available; disclosed as a limitation, not
fabricated).

## Frozen parcel list
See `outputs/validation/expanded_validation_FROZEN_sample.csv` — generated and
saved BEFORE any of these 21 parcels were opened in Google Earth. This file is
never edited after generation; if a parcel proves impossible to check (e.g., no
imagery available at all), the record shows INCONCLUSIVE for that row rather than
being silently dropped and replaced.

## Decision protocol (identical to Pilot v1, applied consistently)
Three-period inspection (pre-conversion / conversion / recovery+persistence),
same TRUE RECOVERY / FALSE POSITIVE / INCONCLUSIVE decision rule, same seasonality
and false-signal controls, same non-blinded-reviewer disclosure. For persistent-
conversion parcels, the "recovery" check is reframed as a false-negative check:
does the parcel show genuine agricultural return at any point after its detected
conversion year that the automated label missed? A persistent-conversion parcel is
recorded as CONFIRMED PERSISTENT (correct negative) unless genuine, persistent
agricultural return is visually confirmed, in which case it is recorded as
FALSE NEGATIVE.
