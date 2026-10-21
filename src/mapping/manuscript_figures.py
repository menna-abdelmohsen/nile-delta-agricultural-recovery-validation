"""Figures 2 and 3 for the ERURJ submission (2026-10-20)."""
import json, pathlib
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT = pathlib.Path(__file__).resolve().parents[2]; FIG = ROOT / "outputs/figures"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
# ---- Fig 2: Sentinel-2 annual state vs visual verdict, 30 visually inspected parcels
d = pd.read_csv(ROOT / "outputs/validation/s2_vs_visual_census.csv")
lab = {"TRUE RECOVERY": "True recovery", "FALSE POSITIVE": "False positive", "INCONCLUSIVE": "Inconclusive",
       "CONFIRMED PERSISTENT": "Persistent,\nconfirmed", "AMBIGUOUS (conversion questionable)": "Persistent,\nconversion\nquestionable"}
order = list(lab)
d["g"] = d.reviewer1.map(order.index); d = d.sort_values(["g", "event_id"]).reset_index(drop=True)
code = {"A": 2, "N": 0, "W": 1, "U": 3}
M = np.array([[code[c] for c in s] for s in d.s2_states_2017_2025])
cmap = ListedColormap(["#c9a26b", "#4a90c2", "#4c9a50", "#e6e6e6"])
fig, ax = plt.subplots(figsize=(7.2, 8.0))
ax.imshow(M, cmap=cmap, vmin=0, vmax=3, aspect="auto")
ax.set_xticks(range(9)); ax.set_xticklabels(range(2017, 2026), rotation=90)
ax.set_yticks(range(len(d))); ax.set_yticklabels([f"{e}  ({v.replace('_', ' ').lower()})" for e, v in zip(d.event_id, d.s2_verdict)], fontsize=7)
for i, c in enumerate(d.conversion_year):
    ax.plot([c - 2017 - 0.5] * 2, [i - 0.5, i + 0.5], color="k", lw=1.6)
prev = None
for i, g in enumerate(d.reviewer1):
    if g != prev:
        if i: ax.axhline(i - 0.5, color="white", lw=3)
        ax.text(8.8, i - 0.4, lab[g], fontsize=7.5, va="top", fontweight="bold")
        prev = g
ax.set_xlim(-0.5, 8.5)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#4c9a50", label="Agricultural"), Patch(color="#c9a26b", label="Non-agricultural"), Patch(color="#e6e6e6", label="Unknown (<50% valid pixels)")],
          loc="upper center", bbox_to_anchor=(0.3, -0.07), ncol=3, frameon=False)
ax.set_title("Sentinel-2 annual state (black bar = Esri/IO conversion year);\nright: visual verdict", fontsize=9)
fig.subplots_adjust(left=0.40, right=0.74, top=0.94, bottom=0.10)
fig.savefig(FIG / "fig2_s2_vs_visual.png", dpi=300); plt.close(fig)
# ---- Fig 3: PR-AUC with CIs, current vs period-matched OSM
a = json.load(open(ROOT / "outputs/metrics/baseline_models_spatial_cv.json"))
b = json.load(open(ROOT / "outputs/metrics/exp17_period_matched_osm.json"))
arms = [("RS only (NDVI)", a["RS_only_historical_ndvi"]), ("No RS, current OSM", a["no_RS_gis_geom_env_temporal"]),
        ("No RS, 2019 OSM", b["no_RS_period_matched_osm"]), ("All features, current OSM", a["all_features_RS_plus_GIS_etc"]),
        ("All features, 2019 OSM", b["all_features_period_matched_osm"])]
models = [("logistic_regression", "Logistic regression"), ("random_forest", "Random forest"), ("xgboost", "XGBoost"), ("lightgbm", "LightGBM")]
cols = ["#7f7f7f", "#1f77b4", "#aec7e8", "#d62728", "#ff9896"]
fig, ax = plt.subplots(figsize=(7.2, 3.6))
w = 0.16
for j, (name, res) in enumerate(arms):
    for i, (k, _) in enumerate(models):
        r = res[k]; x = i + (j - 2) * w
        ax.errorbar(x, r["pr_auc"], yerr=[[r["pr_auc"] - r["pr_auc_95ci"]["ci_low"]], [r["pr_auc_95ci"]["ci_high"] - r["pr_auc"]]],
                    fmt="o", color=cols[j], ms=4, capsize=2, lw=1, label=name if i == 0 else None)
ax.axhline(9 / 209, color="k", ls=":", lw=1); ax.text(3.45, 9 / 209 + 0.015, "base rate 0.043", fontsize=7, ha="right")
ax.set_xticks(range(4)); ax.set_xticklabels([m for _, m in models]); ax.set_ylabel("PR-AUC (95% bootstrap CI)"); ax.set_ylim(0, 1.05)
ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "fig3_model_prauc.png", dpi=300); plt.close(fig)
print("ok")

# ---- Fig 1: complete census (redrawn from the frozen census numbers, legend outside the bars)
tiers = ["Tier A\n(n=4)", "Tier B\n(n=5)", "Tier C\n(n=9)"]
tr, fp, inc = np.array([0, 2, 0]), np.array([2, 2, 8]), np.array([2, 1, 1])
C = {"True recovery": "#2ca02c", "False positive": "#d62728", "Inconclusive": "#8c8c8c"}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.4))
bot = np.zeros(3)
for (k, c), v in zip(C.items(), (tr, fp, inc)):
    a1.bar(tiers, v, bottom=bot, color=c, width=0.6, label=k)
    for x, (b0, vv) in enumerate(zip(bot, v)):
        if vv: a1.text(x, b0 + vv / 2, str(vv), ha="center", va="center", color="white", fontweight="bold")
    bot += v
a1.set_ylabel("Recovery candidates"); a1.set_title("(a) By WorldCover-agreement tier", fontsize=9); a1.set_ylim(0, 10)
cnt = [2, 12, 4]; area = [11.0, 70.0, 19.0]; x = np.arange(3)
a2.bar(x - 0.2, [c / 18 * 100 for c in cnt], 0.4, color=list(C.values()), label="% of candidates")
a2.bar(x + 0.2, area, 0.4, color=list(C.values()), alpha=0.5, hatch="//", label="% of candidate area")
for i in range(3):
    a2.text(i - 0.2, cnt[i] / 18 * 100 + 1.5, f"{cnt[i]/18*100:.1f}%", ha="center", fontsize=7)
    a2.text(i + 0.2, area[i] + 1.5, f"{area[i]:.1f}%", ha="center", fontsize=7)
a2.set_xticks(x); a2.set_xticklabels(list(C)); a2.set_ylabel("Percent"); a2.set_ylim(0, 85)
a2.set_title("(b) Share of candidates vs. share of area", fontsize=9)
h, l = a1.get_legend_handles_labels()
from matplotlib.patches import Patch
fig.legend(h + [Patch(facecolor="white", edgecolor="k", label="solid = count"), Patch(facecolor="white", edgecolor="k", hatch="//", label="hatched = area")],
           l + ["solid = count", "hatched = area"], loc="lower center", ncol=5, fontsize=7.5, frameon=False)
for a in (a1, a2): a.spines[["top", "right"]].set_visible(False)
fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(FIG / "fig1_census.png", dpi=300); plt.close(fig)
