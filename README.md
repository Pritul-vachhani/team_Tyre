# Team Tyre - Environment Setup
Spring 2026 Team-7

## Future TODO (Roadmap for Next Iterations)
1. Try baseline ML models first: Linear Regression, Random Forest, XGBoost, LightGBM, and CatBoost.
2. Try deep learning models for tabular data: MLP, TabTransformer, and FT-Transformer.
3. Compare CPU vs GPU training speed (especially XGBoost/LightGBM with CUDA when available).
4. Add experiment tracking (for example: MLflow or Weights & Biases) to compare model versions.
5. Build an LLM interface that converts natural-language driving descriptions into model-ready features.
6. Add a vehicle-spec enrichment step for unseen cars (fetch curb weight, power, etc. from trusted sources).
7. Wrap the final model in a prediction API (FastAPI) for frontend integration.
8. Add uncertainty estimates so the app can show confidence with each prediction.


### Main features
```
core_features = [
    "current_tread_depth(mm)",
    "Standard_tread_depth(mm)",
    "kilometers_driven(km)",
    "tread_wear_rating (UTQG)",
    "average_inflation_pressure(psi)",
    "recommended_inflation_pressure(psi)",
]
```

### Add extra context features that can improve prediction quality.
```
additional_features = [
    "vehicle_sprung_mass(kg)",
    "vehicle_acceleration(0-100 km/h in seconds)",
    "maximum_power(hp)",
    "maximum_torque(N/m)",
    "maximum_speed (km/h)",
    "vehicle_mileage(mpg)",
    "average_tread_temperature(celsius)",
    "tyre_age(years)",
    "number_of_punctures",
    "expected_tyre_life(km)",
    "retreaded",
    "road_condition",
    "weather_condition",
    "axle_type(driven/dead)",
    "vehicle_model",
    "fuel_type",
    "transmission_type",
    "tyre_brand",
    "tyre_size",
    "tread_material",
    "country",
]
```


This project uses Python `3.12.13`.

## 1. Prerequisites
- Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda.
- Make sure `python --version` can use `3.12.13` in your environment.

## 2. Create and activate conda environment
```bash
conda create -n team_tyre python=3.12.13 -y
conda activate team_tyre
```

## 3. Install project dependencies
```bash
pip install -r requirements.txt
```

## 4. Run Jupyter for notebook development
```bash
jupyter lab
```

Then open:
- `dataset_clean_and_setup.ipynb`

## 5. Dataset location
Place the dataset file in the project root with this exact filename:
- `Synthetic Automobile Tyre RUL Data.csv`

## 6. Optional GPU note
- You can train models on GPU later (for example XGBoost with `device='cuda'`).
- Data cleaning steps in the current notebook mostly run on CPU.
