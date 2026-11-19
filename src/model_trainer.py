"""ML model training, evaluation, and comparison."""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
)
import time

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except ImportError:
    LGBMClassifier = None

import config


def _get_model(name: str):
    params = config.MODEL_CONFIGS[name]
    if name == "RandomForest":
        return RandomForestClassifier(**params)
    if name == "XGBoost":
        if XGBClassifier is None:
            raise ImportError("xgboost not installed")
        return XGBClassifier(**params, use_label_encoder=False, eval_metric="logloss")
    if name == "LightGBM":
        if LGBMClassifier is None:
            raise ImportError("lightgbm not installed")
        return LGBMClassifier(**params, verbose=-1)
    if name == "SVM":
        return SVC(**params)
    raise ValueError(f"Unknown model: {name}")


def train_and_evaluate(df: pd.DataFrame, target_col: str = "label",
                       models_to_train: list[str] | None = None) -> dict:
    if models_to_train is None:
        models_to_train = list(config.MODEL_CONFIGS.keys())

    feature_cols = [c for c in df.columns if c not in (target_col, "url")]
    X = df[feature_cols].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}
    for name in models_to_train:
        print(f"\nTraining {name}...")
        try:
            model = _get_model(name)
        except ImportError as e:
            print(f"  Skipping {name}: {e}")
            continue

        use_scaled = name == "SVM"
        Xtr = X_train_scaled if use_scaled else X_train
        Xte = X_test_scaled if use_scaled else X_test

        start = time.time()
        model.fit(Xtr, y_train)
        train_time = time.time() - start

        start = time.time()
        y_pred = model.predict(Xte)
        predict_time = time.time() - start

        y_proba = model.predict_proba(Xte)[:, 1] if hasattr(model, "predict_proba") else None

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1_score": f1_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_proba) if y_proba is not None else None,
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "train_time_sec": round(train_time, 3),
            "predict_time_sec": round(predict_time, 3),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
        }

        cv_scores = cross_val_score(model, Xtr, y_train, cv=5, scoring="f1")
        metrics["cv_f1_mean"] = round(cv_scores.mean(), 4)
        metrics["cv_f1_std"] = round(cv_scores.std(), 4)

        model_path = os.path.join(config.MODELS_DIR, f"{name}.pkl")
        joblib.dump(model, model_path)

        results[name] = metrics
        print(f"  Accuracy: {metrics['accuracy']:.4f} | F1: {metrics['f1_score']:.4f} | AUC: {metrics.get('roc_auc', 'N/A')}")

    scaler_path = os.path.join(config.MODELS_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)

    meta = {"feature_columns": feature_cols, "models_trained": list(results.keys())}
    with open(os.path.join(config.MODELS_DIR, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    report_path = os.path.join(config.REPORTS_DIR, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nReport saved to {report_path}")

    return results


def load_model(name: str):
    return joblib.load(os.path.join(config.MODELS_DIR, f"{name}.pkl"))


def compare_models(results: dict) -> pd.DataFrame:
    rows = []
    for name, metrics in results.items():
        rows.append({
            "Model": name,
            "Accuracy": metrics["accuracy"],
            "Precision": metrics["precision"],
            "Recall": metrics["recall"],
            "F1 Score": metrics["f1_score"],
            "ROC-AUC": metrics.get("roc_auc", "N/A"),
            "CV F1 Mean": metrics["cv_f1_mean"],
            "Train Time (s)": metrics["train_time_sec"],
            "Predict Time (s)": metrics["predict_time_sec"],
        })
    return pd.DataFrame(rows).sort_values("F1 Score", ascending=False)
