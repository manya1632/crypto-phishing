"""Script to train models on the phishing dataset."""

import sys
from src.dataset_loader import load_csv_dataset, prepare_dataset, save_processed
from src.feature_extractor import extract_features_batch
from src.model_trainer import train_and_evaluate, compare_models


def main():
    print("=" * 60)
    print("Phishing Detection - Model Training Pipeline")
    print("=" * 60)

    print("\n[1/4] Loading dataset...")
    df = load_csv_dataset()
    df = prepare_dataset(df)

    print("\n[2/4] Extracting features...")
    features_df = extract_features_batch(
        df["url"].tolist(),
        df["label"].tolist(),
        include_content=False,
        include_ssl=False,
    )
    save_processed(features_df)

    print("\n[3/4] Training models...")
    results = train_and_evaluate(features_df)

    print("\n[4/4] Model comparison:")
    comparison = compare_models(results)
    print(comparison.to_string(index=False))

    best = comparison.iloc[0]["Model"]
    print(f"\nBest model: {best}")
    print("Done. Models saved to models/")


if __name__ == "__main__":
    main()
