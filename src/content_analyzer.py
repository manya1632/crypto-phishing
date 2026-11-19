"""Webpage content feature extraction."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import config


def fetch_page(url: str) -> tuple[str | None, int]:
    try:
        resp = requests.get(url, timeout=config.REQUEST_TIMEOUT, allow_redirects=True)
        return resp.text, resp.status_code
    except Exception:
        return None, -1


def extract_content_features(url: str) -> dict:
    features = {
        "num_external_links": 0,
        "num_internal_links": 0,
        "external_link_ratio": 0.0,
        "num_forms": 0,
        "has_password_field": 0,
        "has_hidden_fields": 0,
        "num_iframes": 0,
        "num_scripts": 0,
        "num_external_scripts": 0,
        "has_favicon": 0,
        "has_title": 0,
        "title_match_domain": 0,
        "num_images": 0,
        "num_meta_tags": 0,
        "page_length": 0,
        "num_redirects": 0,
        "has_login_form": 0,
        "status_code": -1,
    }

    html, status = fetch_page(url)
    features["status_code"] = status
    if not html:
        return features

    features["page_length"] = len(html)
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlparse(url)
    domain = parsed.netloc

    links = soup.find_all("a", href=True)
    for link in links:
        href = link["href"]
        link_parsed = urlparse(urljoin(url, href))
        if link_parsed.netloc and link_parsed.netloc != domain:
            features["num_external_links"] += 1
        else:
            features["num_internal_links"] += 1

    total_links = features["num_external_links"] + features["num_internal_links"]
    if total_links > 0:
        features["external_link_ratio"] = features["num_external_links"] / total_links

    forms = soup.find_all("form")
    features["num_forms"] = len(forms)
    for form in forms:
        if form.find("input", {"type": "password"}):
            features["has_password_field"] = 1
            features["has_login_form"] = 1
        if form.find("input", {"type": "hidden"}):
            features["has_hidden_fields"] = 1

    features["num_iframes"] = len(soup.find_all("iframe"))

    scripts = soup.find_all("script")
    features["num_scripts"] = len(scripts)
    for script in scripts:
        src = script.get("src", "")
        if src:
            script_parsed = urlparse(urljoin(url, src))
            if script_parsed.netloc and script_parsed.netloc != domain:
                features["num_external_scripts"] += 1

    features["has_favicon"] = int(bool(soup.find("link", rel=lambda v: v and "icon" in v)))
    title_tag = soup.find("title")
    features["has_title"] = int(bool(title_tag))
    if title_tag and title_tag.string:
        features["title_match_domain"] = int(domain.split(".")[0].lower() in title_tag.string.lower())

    features["num_images"] = len(soup.find_all("img"))
    features["num_meta_tags"] = len(soup.find_all("meta"))

    return features
