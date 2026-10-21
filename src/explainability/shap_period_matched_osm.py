"""SHAP sensitivity (2026-10-20): identical to shap_analysis.py (logistic
regression, LinearExplainer, Tier A+B, no-RS features) but with the
period-matched 2019 OSM road/canal distances in place of current-OSM ones.
Output: outputs/metrics/shap_feature_importance_period_matched_osm.json"""
import json, pathlib, sys
import numpy as np, shap
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
ROOT = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / "src"))
from models.train_baseline_models import FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL, load_primary_dataset, RANDOM_SEED
swap = {"distance_to_road_m": "distance_to_road_m_2019", "distance_to_irrigation_m": "distance_to_irrigation_m_2019"}
cols = [swap.get(c, c) for c in FEATURE_COLS_GIS_GEOM_ENV_TEMPORAL]
df = load_primary_dataset(); X = StandardScaler().fit_transform(df[cols].to_numpy()); y = df.outcome.to_numpy()
m = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED).fit(X, y)
sv = shap.LinearExplainer(m, X).shap_values(X); imp = np.abs(sv).mean(0)
tab = [{"feature": cols[i], "mean_abs_shap": float(imp[i]), "coef_sign": "+" if m.coef_[0][i] > 0 else "-"} for i in np.argsort(imp)[::-1]]
(ROOT / "outputs/metrics/shap_feature_importance_period_matched_osm.json").write_text(json.dumps({"n": len(df), "n_positive": int(y.sum()), "features": tab}, indent=2))
for t in tab[:8]: print(f"{t['feature']:32s} {t['mean_abs_shap']:.3f} {t['coef_sign']}")
