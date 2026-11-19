"""Combined feature extraction pipeline."""

import pandas as pd
from src.url_analyzer import extract_url_features, get_domain_info
from src.crypto_verifier import extract_ssl_features
from src.content_analyzer import extract_content_features


def extract_all_features(url: str, include_content: bool = True, include_ssl: bool = True) -> dict:
    features = extract_url_features(url)

    domain_info = get_domain_info(url)
    features.update({
        "domain_age_days": domain_info["domain_age_days"],
        "domain_registration_length": domain_info["domain_registration_length"],
    })

    if include_ssl:
        ssl_features = extract_ssl_features(url)
        features.update(ssl_features)

    if include_content:
        content_features = extract_content_features(url)
        features.update(content_features)

    tld = features.pop("tld", "com")
    features["tld_encoded"] = hash(tld) % 1000

    return features


def extract_features_batch(urls: list[str], labels: list[int] | None = None,
                           include_content: bool = False, include_ssl: bool = False) -> pd.DataFrame:
    rows = []
    for i, url in enumerate(urls):
        try:
            feat = extract_all_features(url, include_content=include_content, include_ssl=include_ssl)
        except Exception:
            feat = {"url_length": len(url)}
        feat["url"] = url
        if labels is not None:
            feat["label"] = labels[i]
        rows.append(feat)
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(urls)} URLs")
    return pd.DataFrame(rows)
