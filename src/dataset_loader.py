"""Dataset loading and preprocessing utilities."""

import os
import pandas as pd
import config


def load_csv_dataset(filename: str = "phishing_dataset.csv") -> pd.DataFrame:
    path = os.path.join(config.DATA_RAW, filename)
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")
    return df


def prepare_dataset(df: pd.DataFrame, url_col: str = "url", label_col: str = "label") -> pd.DataFrame:
    df = df[[url_col, label_col]].copy()
    df.columns = ["url", "label"]
    df = df.dropna()
    df = df.drop_duplicates(subset="url")
    df["label"] = df["label"].astype(int)
    print(f"Dataset after cleaning: {len(df)} rows | {df['label'].value_counts().to_dict()}")
    return df


def save_processed(df: pd.DataFrame, filename: str = "features.csv"):
    path = os.path.join(config.DATA_PROCESSED, filename)
    df.to_csv(path, index=False)
    print(f"Saved to {path}")
