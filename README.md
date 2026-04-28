# Team Tyre - Environment Setup
Spring 2026 Team-7

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
