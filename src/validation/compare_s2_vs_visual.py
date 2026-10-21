"""Agreement between the independent Sentinel-2 trajectory evidence and the
visual census (reviewer 1), plus a full-population screen of the 314
persistent-conversion parcels (added 2026-10-20).

Mapping (fixed before comparison):
  S2 RECOVERY                                   -> RECOVERY
  S2 PERSISTENT_NONAG / NOT_AG_BEFORE /
     NO_CONVERSION_SEEN                         -> NO RECOVERY
  S2 UNCLEAR                                    -> UNDETERMINED
  visual TRUE RECOVERY -> RECOVERY; FALSE POSITIVE / CONFIRMED PERSISTENT /
  AMBIGUOUS -> NO RECOVERY; INCONCLUSIVE -> UNDETERMINED
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "validation"
KEY = OUT / "second_reviewer" / "KEY_DO_NOT_SHARE_with_reviewer.csv"

S2MAP = {"RECOVERY": "RECOVERY", "PERSISTENT_NONAG": "NO RECOVERY", "NOT_AG_BEFORE": "NO RECOVERY",
         "NO_CONVERSION_SEEN": "NO RECOVERY", "UNCLEAR": "UNDETERMINED"}
VMAP = {"TRUE RECOVERY": "RECOVERY", "FALSE POSITIVE": "NO RECOVERY", "CONFIRMED PERSISTENT": "NO RECOVERY",
        "AMBIGUOUS (conversion questionable)": "NO RECOVERY", "INCONCLUSIVE": "UNDETERMINED"}


def kappa(a, b):
    a, b = list(a), list(b)
    n = len(a); cats = sorted(set(a) | set(b))
    po = np.mean([x == y for x, y in zip(a, b)])
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return float(po), float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def main():
    s2 = pd.read_csv(OUT / "s2_trajectory_evidence_parcels.csv")
    key = pd.read_csv(KEY)[["event_id", "reviewer1"]]
    d = s2.merge(key, on="event_id", how="left")
    d["s2_call"] = d.s2_verdict.map(S2MAP)
    d["visual_call"] = d.reviewer1.map(VMAP)
    both = d[d.visual_call.notna()].copy()
    out = {}
    out["n_compared"] = int(len(both))
    out["crosstab_visual_vs_s2_verdict"] = pd.crosstab(both.reviewer1, both.s2_verdict).to_dict("index")
    out["agreement_3class"] = dict(zip(("observed", "kappa"), kappa(both.visual_call, both.s2_call)))
    dec = both[(both.visual_call != "UNDETERMINED") & (both.s2_call != "UNDETERMINED")]
    out["agreement_decided_pairs"] = {"n": int(len(dec)), **dict(zip(("observed", "kappa"), kappa(dec.visual_call, dec.s2_call)))}
    rec = d[d.outcome_name == "recovery"]
    out["recovery_candidates_s2"] = rec.s2_verdict.value_counts().to_dict()
    out["recovery_candidates_s2_by_tier"] = pd.crosstab(rec.tier, rec.s2_verdict).to_dict("index")
    per = d[d.outcome_name == "persistent"]
    out["persistent_all_314_s2"] = per.s2_verdict.value_counts().to_dict()
    out["persistent_water_any_year"] = int((per.water_years > 0).sum())
    out["recovery_water_any_year"] = int((rec.water_years > 0).sum())
    both[["event_id", "outcome_name", "tier", "conversion_year", "s2_states_2017_2025", "s2_verdict",
          "reviewer1", "visual_call", "s2_call"]].to_csv(OUT / "s2_vs_visual_census.csv", index=False)
    (OUT / "s2_vs_visual_summary.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))
    print(both[["event_id", "s2_states_2017_2025", "s2_verdict", "reviewer1"]].to_string())


if __name__ == "__main__":
    main()
