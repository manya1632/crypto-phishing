"""Real-time prediction for new URLs."""

import os
import json
import joblib
import pandas as pd
from src.feature_extractor import extract_all_features
import config


class PhishingPredictor:
    def __init__(self, model_name: str = "RandomForest"):
        self.model = joblib.load(os.path.join(config.MODELS_DIR, f"{model_name}.pkl"))
        self.scaler = joblib.load(os.path.join(config.MODELS_DIR, "scaler.pkl"))
        with open(os.path.join(config.MODELS_DIR, "meta.json")) as f:
            meta = json.load(f)
        self.feature_columns = meta["feature_columns"]
        self.model_name = model_name
        self._needs_scaling = model_name == "SVM"

    def predict(self, url: str) -> dict:
        features = extract_all_features(url, include_content=True, include_ssl=True)
        df = pd.DataFrame([features])

        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        df = df[self.feature_columns].fillna(0)

        X = self.scaler.transform(df) if self._needs_scaling else df
        prediction = self.model.predict(X)[0]
        proba = self.model.predict_proba(X)[0] if hasattr(self.model, "predict_proba") else None

        return {
            "url": url,
            "prediction": "phishing" if prediction == 1 else "legitimate",
            "confidence": float(max(proba)) if proba is not None else None,
            "features": features,
        }
