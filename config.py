import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

RANDOM_STATE = 42
TEST_SIZE = 0.2

MODEL_CONFIGS = {
    "RandomForest": {"n_estimators": 200, "max_depth": 20, "random_state": RANDOM_STATE},
    "XGBoost": {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1, "random_state": RANDOM_STATE},
    "LightGBM": {"n_estimators": 200, "max_depth": 15, "learning_rate": 0.1, "random_state": RANDOM_STATE},
    "SVM": {"kernel": "rbf", "C": 1.0, "probability": True, "random_state": RANDOM_STATE},
}

SSL_TIMEOUT = 5
REQUEST_TIMEOUT = 10
