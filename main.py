from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Literal

import httpx
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from lightgbm import LGBMRegressor
from pydantic import BaseModel, Field
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "tirelife models" / "artifacts" / "tyre_rul_cleaned.csv"
MODEL_DIR = ROOT_DIR / "tirelife models" / "artifacts" / "trained_models"

TARGET_COL = "remaining_useful_life(km)"
DEFAULT_MODEL = "lightgbm"

# Keep "normal" model free from obvious target leakage.
LEAKAGE_EXCLUDED_COLS = {
    "expected_tyre_life(km)",
    "km_used_ratio_vs_expected",
}

# Main user fields we ask for in chat before predicting.
REQUIRED_CHAT_FIELDS = [
    "current_tread_depth(mm)",
    "kilometers_driven(km)",
    "average_inflation_pressure(psi)",
    "tyre_age(years)",
]

REQUIRED_CHAT_FIELD_HINTS = {
    "current_tread_depth(mm)": "Current tread depth in mm (example: 4.5 mm)",
    "kilometers_driven(km)": "Total kilometers already driven on this tyre (example: 28000 km)",
    "average_inflation_pressure(psi)": "Average inflation pressure in psi (example: 32 psi)",
    "tyre_age(years)": "Tyre age in years (example: 3 years)",
}

DEFAULT_INTENT_TOKENS = {
    "use defaults",
    "use default",
    "default values",
    "skip",
    "not sure",
    "dont know",
    "don't know",
}


class PredictRequest(BaseModel):
    features: dict[str, Any] = Field(default_factory=dict)
    model: Literal["lightgbm", "deeplearning_test"] = DEFAULT_MODEL


class PredictResponse(BaseModel):
    model: str
    predicted_rul_km: float
    predicted_rul_miles: float
    defaults_used: list[str]
    defaults_used_count: int
    normalized_features: dict[str, Any]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    model: Literal["lightgbm", "deeplearning_test"] = DEFAULT_MODEL
    force_predict: bool = False


class ChatResponse(BaseModel):
    session_id: str
    needs_follow_up: bool
    assistant_message: str
    missing_fields: list[str]
    extractor: str
    parsed_features: dict[str, Any]
    prediction: PredictResponse | None = None


class HealthResponse(BaseModel):
    status: str
    dataset_path: str
    models_available: list[str]
    required_chat_fields: list[str]


class TireRULService:
    def __init__(self, data_path: Path, model_dir: Path):
        self.data_path = data_path
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.sessions: dict[str, dict[str, Any]] = {}

        self.defaults: dict[str, Any] = {}
        self.numeric_cols: set[str] = set()
        self.categorical_cols: set[str] = set()
        self.feature_cols_all: list[str] = []
        self.feature_cols_lightgbm: list[str] = []
        self.feature_cols_deep: list[str] = []
        self.models: dict[str, Any] = {}

        self.feature_aliases = {
            "current_tread_depth_mm": "current_tread_depth(mm)",
            "current_tread_depth": "current_tread_depth(mm)",
            "standard_tread_depth_mm": "Standard_tread_depth(mm)",
            "standard_tread_depth": "Standard_tread_depth(mm)",
            "kilometers_driven_km": "kilometers_driven(km)",
            "kilometers_driven": "kilometers_driven(km)",
            "km_driven": "kilometers_driven(km)",
            "tread_wear_rating_utqg": "tread_wear_rating (UTQG)",
            "average_inflation_pressure_psi": "average_inflation_pressure(psi)",
            "recommended_inflation_pressure_psi": "recommended_inflation_pressure(psi)",
            "vehicle_sprung_mass_kg": "vehicle_sprung_mass(kg)",
            "vehicle_acceleration_0_100_km_h_in_seconds": "vehicle_acceleration(0-100 km/h in seconds)",
            "maximum_power_hp": "maximum_power(hp)",
            "maximum_torque_n_m": "maximum_torque(N/m)",
            "maximum_speed_km_h": "maximum_speed (km/h)",
            "vehicle_mileage_mpg": "vehicle_mileage(mpg)",
            "average_tread_temperature_celsius": "average_tread_temperature(celsius)",
            "tyre_age_years": "tyre_age(years)",
            "number_of_punctures": "number_of_punctures",
            "expected_tyre_life_km": "expected_tyre_life(km)",
            "axle_type": "axle_type(driven/dead)",
        }

    def startup(self) -> None:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.data_path}")
        self._load_profile()
        self._load_or_train_models()

    def _profile_nrows(self) -> int | None:
        raw = os.getenv("PROFILE_SAMPLE_ROWS", "220000").strip()
        if raw == "0":
            return None
        try:
            value = int(raw)
            return value if value > 0 else None
        except ValueError:
            return 220000

    def _train_nrows(self) -> int | None:
        raw = os.getenv("TRAIN_SAMPLE_ROWS", "220000").strip()
        if raw == "0":
            return None
        try:
            value = int(raw)
            return value if value > 0 else None
        except ValueError:
            return 220000

    def _load_profile(self) -> None:
        df = pd.read_csv(self.data_path, nrows=self._profile_nrows(), low_memory=False)
        if TARGET_COL not in df.columns:
            raise ValueError(f"Missing target column '{TARGET_COL}' in {self.data_path}")

        self.feature_cols_all = [c for c in df.columns if c != TARGET_COL]

        numeric_cols: list[str] = []
        categorical_cols: list[str] = []
        defaults: dict[str, Any] = {}

        for col in self.feature_cols_all:
            numeric_candidate = pd.to_numeric(df[col], errors="coerce")
            numeric_ratio = float(numeric_candidate.notna().mean())
            if numeric_ratio >= 0.95:
                numeric_cols.append(col)
                defaults[col] = float(numeric_candidate.median(skipna=True))
            else:
                categorical_cols.append(col)
                mode = df[col].dropna().astype(str).str.strip().str.lower().mode()
                defaults[col] = mode.iloc[0] if not mode.empty else "unknown"

        self.numeric_cols = set(numeric_cols)
        self.categorical_cols = set(categorical_cols)
        self.defaults = defaults

        self.feature_cols_lightgbm = [
            col for col in self.feature_cols_all if col not in LEAKAGE_EXCLUDED_COLS
        ]
        self.feature_cols_deep = list(self.feature_cols_lightgbm)

    def _make_training_frame(self, df: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, pd.Series]:
        y = pd.to_numeric(df[TARGET_COL], errors="coerce")
        mask = y.notna()
        y = y.loc[mask].astype(float)

        X = df.loc[mask, feature_cols].copy()
        for col in feature_cols:
            if col in self.numeric_cols:
                X[col] = pd.to_numeric(X[col], errors="coerce").fillna(float(self.defaults[col]))
            else:
                X[col] = (
                    X[col]
                    .astype("string")
                    .str.strip()
                    .str.lower()
                    .fillna(str(self.defaults[col]))
                    .astype("category")
                )

        return X, y

    def _load_or_train_models(self) -> None:
        lgbm_path = self.model_dir / "lightgbm_normal_non_leakage.joblib"
        deep_path = self.model_dir / "deeplearning_test_mlp.joblib"

        if lgbm_path.exists():
            try:
                self.models["lightgbm"] = joblib.load(lgbm_path)
            except Exception:
                self.models["lightgbm"] = self._train_lightgbm()
                joblib.dump(self.models["lightgbm"], lgbm_path)
        else:
            self.models["lightgbm"] = self._train_lightgbm()
            joblib.dump(self.models["lightgbm"], lgbm_path)

        if deep_path.exists():
            try:
                self.models["deeplearning_test"] = joblib.load(deep_path)
            except Exception:
                self.models["deeplearning_test"] = self._train_deep_test_model()
                joblib.dump(self.models["deeplearning_test"], deep_path)
        else:
            self.models["deeplearning_test"] = self._train_deep_test_model()
            joblib.dump(self.models["deeplearning_test"], deep_path)

    def _load_training_df(self) -> pd.DataFrame:
        return pd.read_csv(self.data_path, nrows=self._train_nrows(), low_memory=False)

    def _train_lightgbm(self) -> dict[str, Any]:
        df = self._load_training_df()
        X, y = self._make_training_frame(df, self.feature_cols_lightgbm)
        cat_cols = [c for c in self.feature_cols_lightgbm if c in self.categorical_cols]

        model = LGBMRegressor(
            objective="regression",
            random_state=42,
            n_estimators=500,
            learning_rate=0.05,
            num_leaves=63,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.05,
            reg_lambda=0.05,
        )
        model.fit(X, y, categorical_feature=cat_cols)

        return {
            "model": model,
            "feature_cols": list(self.feature_cols_lightgbm),
            "cat_cols": cat_cols,
            "kind": "lightgbm",
        }

    def _train_deep_test_model(self) -> dict[str, Any]:
        df = self._load_training_df()
        if len(df) > 120000:
            df = df.sample(n=120000, random_state=42)

        X, y = self._make_training_frame(df, self.feature_cols_deep)
        cat_cols = [c for c in self.feature_cols_deep if c in self.categorical_cols]
        num_cols = [c for c in self.feature_cols_deep if c in self.numeric_cols]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    num_cols,
                ),
                (
                    "cat",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            (
                                "encoder",
                                OrdinalEncoder(
                                    handle_unknown="use_encoded_value",
                                    unknown_value=-1,
                                ),
                            ),
                        ]
                    ),
                    cat_cols,
                ),
            ],
            remainder="drop",
        )

        model = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "mlp",
                    MLPRegressor(
                        hidden_layer_sizes=(128, 64),
                        activation="relu",
                        learning_rate_init=0.001,
                        max_iter=90,
                        early_stopping=True,
                        random_state=42,
                    ),
                ),
            ]
        )
        model.fit(X, y)

        return {
            "model": model,
            "feature_cols": list(self.feature_cols_deep),
            "cat_cols": cat_cols,
            "kind": "deeplearning_test",
        }

    def _normalize_feature_key(self, raw_key: str) -> str | None:
        key = raw_key.strip()
        if key in self.defaults:
            return key
        compact = (
            key.lower()
            .replace("-", "_")
            .replace(" ", "_")
            .replace("(", "_")
            .replace(")", "")
            .replace("/", "_")
            .replace("%", "pct")
            .replace("__", "_")
        )
        if compact in self.feature_aliases:
            return self.feature_aliases[compact]
        return None

    def _coerce_value(self, feature: str, value: Any) -> Any:
        if value is None:
            return None

        if feature == "retreaded":
            text = str(value).strip().lower()
            if text in {"yes", "y", "true", "1"}:
                return 1.0
            if text in {"no", "n", "false", "0"}:
                return 0.0

        if feature in self.numeric_cols:
            if isinstance(value, (int, float, np.integer, np.floating)):
                return float(value)
            cleaned = str(value).strip().lower().replace(",", "")
            match = re.search(r"-?\d+(\.\d+)?", cleaned)
            if match:
                return float(match.group())
            return None

        return str(value).strip().lower()

    def _derive_engineered_features(self, features: dict[str, Any]) -> None:
        def _safe_float(name: str) -> float:
            value = self._coerce_value(name, features.get(name, self.defaults.get(name)))
            if value is None:
                return float(self.defaults.get(name, 0.0))
            return float(value)

        std_depth = _safe_float("Standard_tread_depth(mm)")
        current_depth = _safe_float("current_tread_depth(mm)")
        avg_pressure = _safe_float("average_inflation_pressure(psi)")
        rec_pressure = _safe_float("recommended_inflation_pressure(psi)")
        km_driven = _safe_float("kilometers_driven(km)")
        expected_life = _safe_float("expected_tyre_life(km)")

        tread_depth_used_mm = max(0.0, std_depth - current_depth)
        features["tread_depth_used_mm"] = tread_depth_used_mm
        features["tread_depth_used_pct"] = tread_depth_used_mm / std_depth if std_depth > 0 else 0.0
        features["pressure_gap_psi"] = avg_pressure - rec_pressure
        features["pressure_gap_pct"] = (avg_pressure - rec_pressure) / rec_pressure if rec_pressure > 0 else 0.0
        features["km_used_ratio_vs_expected"] = km_driven / expected_life if expected_life > 0 else 0.0

    def normalize_features(self, incoming: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        normalized: dict[str, Any] = {}
        provided_keys: set[str] = set()

        for raw_key, raw_value in incoming.items():
            canonical = self._normalize_feature_key(raw_key)
            if not canonical:
                continue
            coerced = self._coerce_value(canonical, raw_value)
            if coerced is None:
                continue
            normalized[canonical] = coerced
            provided_keys.add(canonical)

        merged = dict(self.defaults)
        merged.update(normalized)
        self._derive_engineered_features(merged)

        defaulted = sorted(
            [
                col
                for col in self.feature_cols_all
                if col not in provided_keys and col in merged
            ]
        )
        return merged, defaulted

    def _predict_from_record(self, model_name: str, record: dict[str, Any]) -> float:
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' is not available")
        payload = self.models[model_name]
        model = payload["model"]
        feature_cols: list[str] = payload["feature_cols"]

        row = pd.DataFrame([{col: record.get(col, self.defaults[col]) for col in feature_cols}])
        for col in feature_cols:
            if col in self.numeric_cols:
                row[col] = pd.to_numeric(row[col], errors="coerce").fillna(float(self.defaults[col]))
            else:
                row[col] = (
                    row[col]
                    .astype("string")
                    .str.strip()
                    .str.lower()
                    .fillna(str(self.defaults[col]))
                    .astype("category")
                )

        pred = float(model.predict(row)[0])
        return max(0.0, pred)

    def predict(self, features: dict[str, Any], model_name: str) -> PredictResponse:
        normalized, defaulted = self.normalize_features(features)
        pred_km = self._predict_from_record(model_name=model_name, record=normalized)
        pred_miles = pred_km * 0.621371
        model_feature_cols = set(self.models[model_name]["feature_cols"])
        model_defaulted = [col for col in defaulted if col in model_feature_cols]

        return PredictResponse(
            model=model_name,
            predicted_rul_km=round(pred_km, 2),
            predicted_rul_miles=round(pred_miles, 2),
            defaults_used=model_defaulted,
            defaults_used_count=len(model_defaulted),
            normalized_features=normalized,
        )

    def _extract_with_gemini(self, user_text: str) -> dict[str, Any]:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return {}

        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        prompt = f"""
You extract tyre prediction features from user text.
Return only valid JSON object, no markdown, no extra keys.
If value not present, use null.

Allowed keys:
{json.dumps(self.feature_cols_all, ensure_ascii=True)}

Rules:
- Numeric fields must be numbers.
- Keep categorical fields lower-case strings.
- Convert miles to kilometers for any distance field.
- Convert booleans like retreaded yes/no into 1 or 0.

User message:
{user_text}
""".strip()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": api_key}
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, params=params, json=body)
            resp.raise_for_status()
            payload = resp.json()

        candidates = payload.get("candidates", [])
        if not candidates:
            return {}
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return {}

        raw_text = parts[0].get("text", "").strip()
        if not raw_text:
            return {}

        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        extracted = json.loads(raw_text)
        if isinstance(extracted, dict):
            return extracted
        return {}

    def _extract_with_regex(self, user_text: str) -> dict[str, Any]:
        text = user_text.lower().replace(",", "")
        parsed: dict[str, Any] = {}

        def _match(pattern: str) -> re.Match[str] | None:
            return re.search(pattern, text, flags=re.IGNORECASE)

        m = _match(r"(?:current\s*)?tread(?:\s*depth)?[^\d]{0,12}(-?\d+(?:\.\d+)?)\s*mm")
        if not m:
            m = _match(r"(-?\d+(?:\.\d+)?)\s*mm[^\n.]{0,20}tread")
        if m:
            parsed["current_tread_depth(mm)"] = float(m.group(1))

        m = _match(r"(?:standard|new|original)\s*tread(?:\s*depth)?[^\d]{0,12}(-?\d+(?:\.\d+)?)\s*mm")
        if m:
            parsed["Standard_tread_depth(mm)"] = float(m.group(1))

        m = _match(r"(?:driven|odometer|odo|mileage)[^\d]{0,20}(-?\d+(?:\.\d+)?)\s*(km|kilometers|mi|miles)")
        if m:
            value = float(m.group(1))
            unit = m.group(2).lower()
            parsed["kilometers_driven(km)"] = value * 1.60934 if unit in {"mi", "miles"} else value

        m = _match(r"(?:average\s*)?(?:inflation\s*)?pressure[^\d]{0,12}(-?\d+(?:\.\d+)?)\s*psi")
        if m:
            parsed["average_inflation_pressure(psi)"] = float(m.group(1))

        m = _match(r"(?:recommended|target)\s*(?:inflation\s*)?pressure[^\d]{0,12}(-?\d+(?:\.\d+)?)\s*psi")
        if m:
            parsed["recommended_inflation_pressure(psi)"] = float(m.group(1))

        m = _match(r"(?:tyre|tire)?\s*age[^\d]{0,12}(-?\d+(?:\.\d+)?)\s*(?:years?|yrs?)")
        if not m:
            m = _match(r"(-?\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:old)?")
        if m:
            parsed["tyre_age(years)"] = float(m.group(1))

        m = _match(r"(-?\d+(?:\.\d+)?)\s*(?:punctures?|flats?)")
        if m:
            parsed["number_of_punctures"] = float(m.group(1))

        if "retreaded yes" in text or "retreaded: yes" in text or "retreaded true" in text:
            parsed["retreaded"] = 1
        if "retreaded no" in text or "retreaded: no" in text or "retreaded false" in text:
            parsed["retreaded"] = 0

        road_tokens = {
            "smooth": "smooth",
            "rough": "rough",
            "mixed": "mixed",
            "wet": "wet",
        }
        for token, canonical in road_tokens.items():
            if token in text:
                parsed["road_condition"] = canonical
                break

        weather_tokens = {
            "dry": "dry",
            "rain": "rainy",
            "snow": "snowy",
            "humid": "tropical and humid",
            "mixed": "mixed conditions",
        }
        for token, canonical in weather_tokens.items():
            if token in text:
                parsed["weather_condition"] = canonical
                break

        if "driven axle" in text or "driven wheels" in text:
            parsed["axle_type(driven/dead)"] = "driven"
        if "dead axle" in text or "non driven axle" in text:
            parsed["axle_type(driven/dead)"] = "dead"

        brand_match = _match(r"(?:tyre|tire)\s*brand[^\w]{0,4}([a-z0-9 +\\-/]{3,40})")
        if brand_match:
            parsed["tyre_brand"] = brand_match.group(1).strip()

        return parsed

    def extract_features(self, user_text: str) -> tuple[dict[str, Any], str]:
        extracted: dict[str, Any] = {}
        extractor = "regex"

        try:
            gemini = self._extract_with_gemini(user_text)
            if gemini:
                extracted = gemini
                extractor = "gemini"
        except Exception:
            extracted = {}
            extractor = "regex"

        if not extracted:
            extracted = self._extract_with_regex(user_text)

        # Keep only values that came from user extraction (not defaults)
        cleaned: dict[str, Any] = {}
        for key, value in extracted.items():
            canonical = self._normalize_feature_key(key)
            if not canonical:
                continue
            coerced = self._coerce_value(canonical, value)
            if coerced is not None:
                cleaned[canonical] = coerced

        # If a parsed value contributes to engineered fields, include the derived fields.
        if cleaned:
            with_derived = dict(cleaned)
            merged = dict(self.defaults)
            merged.update(cleaned)
            self._derive_engineered_features(merged)
            for col in (
                "tread_depth_used_mm",
                "tread_depth_used_pct",
                "pressure_gap_psi",
                "pressure_gap_pct",
                "km_used_ratio_vs_expected",
            ):
                with_derived[col] = merged[col]
            cleaned = with_derived

        return cleaned, extractor

    def get_or_create_session(self, session_id: str | None) -> tuple[str, dict[str, Any]]:
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        new_id = session_id or str(uuid.uuid4())
        if new_id not in self.sessions:
            self.sessions[new_id] = {"features": {}, "model": DEFAULT_MODEL}
        return new_id, self.sessions[new_id]

    def should_use_defaults(self, user_text: str, force_predict: bool) -> bool:
        if force_predict:
            return True
        lowered = user_text.lower()
        return any(token in lowered for token in DEFAULT_INTENT_TOKENS)

    def chat(self, request: ChatRequest) -> ChatResponse:
        session_id, session = self.get_or_create_session(request.session_id)
        session["model"] = request.model

        parsed_features, extractor = self.extract_features(request.message)
        session["features"].update(parsed_features)

        missing_required = [
            field
            for field in REQUIRED_CHAT_FIELDS
            if field not in session["features"] or session["features"][field] in ("", None)
        ]

        if missing_required and not self.should_use_defaults(request.message, request.force_predict):
            hints = [f"- {REQUIRED_CHAT_FIELD_HINTS[field]}" for field in missing_required]
            assistant_message = (
                "I can predict once I have a few key values.\n"
                + "\n".join(hints)
                + "\n\nIf you prefer, reply with 'use defaults' and I will auto-fill missing fields."
            )
            return ChatResponse(
                session_id=session_id,
                needs_follow_up=True,
                assistant_message=assistant_message,
                missing_fields=missing_required,
                extractor=extractor,
                parsed_features=parsed_features,
                prediction=None,
            )

        prediction = self.predict(features=session["features"], model_name=session["model"])
        assistant_message = (
            f"Estimated remaining tyre life: {prediction.predicted_rul_km:,.0f} km "
            f"({prediction.predicted_rul_miles:,.0f} miles) using {prediction.model}."
        )
        if prediction.defaults_used_count:
            assistant_message += (
                f" I auto-filled {prediction.defaults_used_count} feature(s) with dataset defaults."
            )

        return ChatResponse(
            session_id=session_id,
            needs_follow_up=False,
            assistant_message=assistant_message,
            missing_fields=[],
            extractor=extractor,
            parsed_features=parsed_features,
            prediction=prediction,
        )


service = TireRULService(data_path=DATA_PATH, model_dir=MODEL_DIR)

app = FastAPI(title="TireLife FastAPI Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    service.startup()


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        dataset_path=str(service.data_path),
        models_available=sorted(service.models.keys()),
        required_chat_fields=REQUIRED_CHAT_FIELDS,
    )


@app.post("/api/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        return service.predict(features=request.features, model_name=request.model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return service.chat(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
