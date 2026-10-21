"""Arabic-labelled versions of Figures 1-3 for the Arabic manuscript (2026-10-20)."""
import json, pathlib
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
ROOT = pathlib.Path(__file__).resolve().parents[2]; FIG = ROOT / "outputs/figures"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
A = lambda s: s  # matplotlib >= 3.11 shapes and orders Arabic natively
# ---- Fig 1
tiers = [A("المستوى A\n(n=4)"), A("المستوى B\n(n=5)"), A("المستوى C\n(n=9)")]
tiers = [A(t) for t in ["المستوى A (4)", "المستوى B (5)", "المستوى C (9)"]]
tr, fp, inc = np.array([0, 2, 0]), np.array([2, 2, 8]), np.array([2, 1, 1])
C = {"عودة حقيقية": "#2ca02c", "إيجابية خاطئة": "#d62728", "غير محسومة": "#8c8c8c"}
fig, (a2, a1) = plt.subplots(1, 2, figsize=(7.2, 3.4))
bot = np.zeros(3)
for (k, c), v in zip(C.items(), (tr, fp, inc)):
    a1.bar(tiers, v, bottom=bot, color=c, width=0.6, label=A(k))
    for x, (b0, vv) in enumerate(zip(bot, v)):
        if vv: a1.text(x, b0 + vv / 2, str(vv), ha="center", va="center", color="white", fontweight="bold")
    bot += v
a1.set_ylabel(A("عدد الحالات المرشحة")); a1.set_title(A("(أ) حسب مستوى الاتفاق مع WorldCover"), fontsize=9); a1.set_ylim(0, 10)
cnt = [2, 12, 4]; area = [11.0, 70.0, 19.0]; x = np.arange(3)
a2.bar(x - 0.2, [c / 18 * 100 for c in cnt], 0.4, color=list(C.values()))
a2.bar(x + 0.2, area, 0.4, color=list(C.values()), alpha=0.5, hatch="//")
for i in range(3):
    a2.text(i - 0.2, cnt[i] / 18 * 100 + 1.5, f"{cnt[i]/18*100:.1f}%", ha="center", fontsize=7)
    a2.text(i + 0.2, area[i] + 1.5, f"{area[i]:.1f}%", ha="center", fontsize=7)
a2.set_xticks(x); a2.set_xticklabels([A(k) for k in C]); a2.set_ylabel(A("النسبة المئوية")); a2.set_ylim(0, 85)
a2.set_title(A("(ب) النصيب من العدد مقابل النصيب من المساحة"), fontsize=9)
h, l = a1.get_legend_handles_labels()
fig.legend(h + [Patch(facecolor="white", edgecolor="k"), Patch(facecolor="white", edgecolor="k", hatch="//")],
           l + [A("مصمت = العدد"), A("مخطط = المساحة")], loc="lower center", ncol=5, fontsize=7.5, frameon=False)
for a in (a1, a2): a.spines[["top", "right"]].set_visible(False)
fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(FIG / "fig1_census_ar.png", dpi=300); plt.close(fig)
# ---- Fig 2
d = pd.read_csv(ROOT / "outputs/validation/s2_vs_visual_census.csv")
lab = {"TRUE RECOVERY": "عودة حقيقية", "FALSE POSITIVE": "إيجابية خاطئة", "INCONCLUSIVE": "غير محسومة",
       "CONFIRMED PERSISTENT": "تحويل مستمر\nمؤكد", "AMBIGUOUS (conversion questionable)": "تحويل مستمر\nالتحويل\nمشكوك فيه"}
vtr = {"NOT_AG_BEFORE": "غير زراعية قبل التحويل", "NO_CONVERSION_SEEN": "لا تحويل مرصود", "RECOVERY": "عودة",
       "PERSISTENT_NONAG": "غير زراعية مستمرة", "UNCLEAR": "غير واضحة"}
order = list(lab); d["g"] = d.reviewer1.map(order.index); d = d.sort_values(["g", "event_id"]).reset_index(drop=True)
code = {"A": 2, "N": 0, "W": 1, "U": 3}
M = np.array([[code[c] for c in s] for s in d.s2_states_2017_2025])
cmap = ListedColormap(["#c9a26b", "#4a90c2", "#4c9a50", "#e6e6e6"])
fig, ax = plt.subplots(figsize=(7.2, 8.0))
ax.imshow(M, cmap=cmap, vmin=0, vmax=3, aspect="auto")
ax.set_xticks(range(9)); ax.set_xticklabels(range(2017, 2026), rotation=90)
ax.set_yticks(range(len(d))); ax.set_yticklabels([f"{e}  ({A(vtr[v])})" for e, v in zip(d.event_id, d.s2_verdict)], fontsize=7)
for i, c in enumerate(d.conversion_year):
    ax.plot([c - 2017 - 0.5] * 2, [i - 0.5, i + 0.5], color="k", lw=1.6)
prev = None
for i, g in enumerate(d.reviewer1):
    if g != prev:
        if i: ax.axhline(i - 0.5, color="white", lw=3)
        ax.text(8.8, i - 0.4, "\n".join(A(x) for x in lab[g].split("\n")), fontsize=7.5, va="top", fontweight="bold")
        prev = g
ax.set_xlim(-0.5, 8.5)
ax.legend(handles=[Patch(color="#4c9a50", label=A("زراعية")), Patch(color="#c9a26b", label=A("غير زراعية")), Patch(color="#e6e6e6", label=A("غير معروفة (أقل من 50% بكسلات صالحة)"))],
          loc="upper center", bbox_to_anchor=(0.3, -0.07), ncol=3, frameon=False)
ax.set_title(A("الحالة السنوية من Sentinel-2 (الخط الأسود = سنة التحويل في Esri/IO)") + "\n" + A("يميناً: حكم الفحص البصري"), fontsize=9)
fig.subplots_adjust(left=0.40, right=0.74, top=0.94, bottom=0.10)
fig.savefig(FIG / "fig2_s2_vs_visual_ar.png", dpi=300); plt.close(fig)
# ---- Fig 3
a = json.load(open(ROOT / "outputs/metrics/baseline_models_spatial_cv.json"))
b = json.load(open(ROOT / "outputs/metrics/exp17_period_matched_osm.json"))
arms = [("الاستشعار عن بُعد فقط (NDVI)", a["RS_only_historical_ndvi"]), ("دون استشعار عن بُعد، OSM الحالي", a["no_RS_gis_geom_env_temporal"]),
        ("دون استشعار عن بُعد، OSM 2019", b["no_RS_period_matched_osm"]), ("كل الخصائص، OSM الحالي", a["all_features_RS_plus_GIS_etc"]),
        ("كل الخصائص، OSM 2019", b["all_features_period_matched_osm"])]
models = [("logistic_regression", "الانحدار اللوجستي"), ("random_forest", "الغابة العشوائية"), ("xgboost", "XGBoost"), ("lightgbm", "LightGBM")]
cols = ["#7f7f7f", "#1f77b4", "#aec7e8", "#d62728", "#ff9896"]
fig, ax = plt.subplots(figsize=(7.2, 3.6)); w = 0.16
for j, (name, res) in enumerate(arms):
    for i, (k, _) in enumerate(models):
        r = res[k]; xx = i + (j - 2) * w
        ax.errorbar(xx, r["pr_auc"], yerr=[[r["pr_auc"] - r["pr_auc_95ci"]["ci_low"]], [r["pr_auc_95ci"]["ci_high"] - r["pr_auc"]]],
                    fmt="o", color=cols[j], ms=4, capsize=2, lw=1, label=A(name) if i == 0 else None)
ax.axhline(9 / 209, color="k", ls=":", lw=1); ax.text(3.45, 9 / 209 + 0.015, A("المعدل الأساسي 0.043"), fontsize=7, ha="right")
ax.set_xticks(range(4)); ax.set_xticklabels([A(m) for _, m in models]); ax.set_ylabel(A("PR-AUC (فترة ثقة 95%)")); ax.set_ylim(0, 1.05)
ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "fig3_model_prauc_ar.png", dpi=300); plt.close(fig)
print("ok")
