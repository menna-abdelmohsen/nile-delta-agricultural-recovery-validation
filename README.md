# Reversal-based agricultural recovery detection — complete-census validation (Nile Delta, Egypt)

Code and data accompanying the manuscript *"How Reliable Is Reversal-Based Detection of Agricultural Land Recovery in 10 m Annual Land-Cover Products? A Complete-Census Validation in the Nile Delta, Egypt"* (submitted to the ERU Research Journal).

Four 8.5 × 8.5 km windows in Dakahlia governorate (El-Bagalat, Mit Salsil, Talkha, Sherbin) were labelled from the Esri/Impact Observatory 10 m annual land-cover product (2017–2024). The pipeline produced 18 recovery candidates (cropland → built/bare → cropland) and 314 persistent-conversion parcels. Every recovery candidate was checked against dated Google Earth imagery: 2 genuine, 12 false positives, 4 inconclusive.

## Contents

| Path | What it is |
|---|---|
| `src/data_acquisition/` | Public COG/STAC downloads (Esri/IO, WorldCover, DEM, Sentinel-2) and OpenStreetMap extraction, including the 1 January 2019 historical snapshot |
| `src/historical_agriculture/`, `src/labeling/` | Historical cropland mask, conversion detection, recovery/persistent labels, WorldCover confidence tiers, threshold sensitivity |
| `src/feature_engineering/` | Parcel-level feature table |
| `src/validation/` | Spatial blocks, Moran's I, independent Sentinel-2 trajectory check and its comparison with the visual census |
| `src/models/`, `src/explainability/`, `src/evaluation/` | Spatially blocked model comparison (incl. period-matched OSM), SHAP, statistical tests |
| `src/mapping/` | Manuscript figures |
| `data/processed/` | `master_dataset_all_windows.csv` (332 parcels, all features) |
| `data/labels/` | Parcel-id, conversion-year, trajectory-label and confidence-tier rasters per window |
| `data/raw/*/osm_*` | OSM roads/canals: current extract and 2019-01-01 snapshot |
| `outputs/validation/` | Frozen visual-validation sample, protocol and parcel-by-parcel results, error taxonomy, sensitivity analyses, Sentinel-2 trajectory results |
| `outputs/metrics/`, `outputs/tables/`, `outputs/figures/` | Model metrics, tables and figures |
| `protocol/experiment_registry.csv` | Every experiment run, with status |

Large rasters (Esri/IO, WorldCover, DEM, Sentinel-2 composites) are not stored here; they are re-downloaded from public, unauthenticated sources by the scripts in `src/data_acquisition/`.

## Reproducing

```bash
pip install -r requirements.txt
python -m src.data_acquisition.public_cog_extraction
python -m src.data_acquisition.sentinel2_multiindex_extraction
python -m src.data_acquisition.osm_historical_extraction
python -m src.historical_agriculture.build_mask
python -m src.labeling.build_labels
python -m src.labeling.verify_against_worldcover
python -m src.labeling.assign_confidence_tiers
python -m src.feature_engineering.build_master_dataset
python -m src.validation.s2_trajectory_evidence
python -m src.models.train_baseline_models
python -m src.models.run_exp17_period_matched_osm
python -m src.explainability.shap_period_matched_osm
python src/mapping/manuscript_figures.py
```

Model results are reproduced exactly with the pinned versions in `requirements.txt` (scikit-learn 1.8.0, random seed 42).

## License

Code: MIT License. Derived data: CC BY 4.0. Source datasets remain under their providers' licences (Esri/IO and ESA WorldCover CC BY 4.0; Copernicus Sentinel data; OpenStreetMap ODbL).
