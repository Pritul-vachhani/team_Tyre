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
