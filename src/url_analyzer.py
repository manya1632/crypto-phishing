"""URL feature extraction and analysis."""

import re
import socket
from urllib.parse import urlparse, parse_qs
import whois
from datetime import datetime
import tldextract


def extract_url_features(url: str) -> dict:
    parsed = urlparse(url if "://" in url else f"http://{url}")
    ext = tldextract.extract(url)
    features = {}

    features["url_length"] = len(url)
    features["hostname_length"] = len(parsed.hostname or "")
    features["path_length"] = len(parsed.path)
    features["num_dots"] = url.count(".")
    features["num_hyphens"] = url.count("-")
    features["num_underscores"] = url.count("_")
    features["num_slashes"] = url.count("/")
    features["num_query_params"] = len(parse_qs(parsed.query))
    features["num_fragments"] = 1 if parsed.fragment else 0
    features["num_at_symbols"] = url.count("@")
    features["has_ip_address"] = int(_has_ip(parsed.hostname or ""))
    features["has_https"] = int(parsed.scheme == "https")
    features["num_subdomains"] = max(len(ext.subdomain.split(".")) - 1, 0) if ext.subdomain else 0
    features["path_depth"] = parsed.path.strip("/").count("/") + 1 if parsed.path.strip("/") else 0
    features["has_suspicious_words"] = int(_has_suspicious_words(url))
    features["digit_ratio"] = sum(c.isdigit() for c in url) / max(len(url), 1)
    features["letter_ratio"] = sum(c.isalpha() for c in url) / max(len(url), 1)
    features["special_char_ratio"] = sum(not c.isalnum() for c in url) / max(len(url), 1)
    features["has_port"] = int(parsed.port is not None)
    features["is_shortened"] = int(_is_shortened(ext.domain, ext.suffix))
    features["tld"] = ext.suffix

    return features


def _has_ip(hostname: str) -> bool:
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(pattern, hostname):
        return True
    if hostname.startswith("0x") or hostname.startswith("["):
        return True
    return False


SUSPICIOUS_WORDS = [
    "login", "signin", "verify", "account", "update", "secure",
    "banking", "confirm", "password", "credential", "suspend",
    "alert", "notification", "paypal", "ebay", "amazon",
]


def _has_suspicious_words(url: str) -> bool:
    url_lower = url.lower()
    return any(word in url_lower for word in SUSPICIOUS_WORDS)


SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly", "shorturl.at"}


def _is_shortened(domain: str, suffix: str) -> bool:
    return f"{domain}.{suffix}" in SHORTENERS


def get_domain_info(url: str) -> dict:
    ext = tldextract.extract(url)
    domain = f"{ext.domain}.{ext.suffix}"
    info = {"domain_age_days": -1, "domain_registration_length": -1, "registrar": "unknown"}
    try:
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        expiration = w.expiration_date
        if isinstance(expiration, list):
            expiration = expiration[0]
        if creation:
            info["domain_age_days"] = (datetime.now() - creation).days
        if creation and expiration:
            info["domain_registration_length"] = (expiration - creation).days
        if w.registrar:
            info["registrar"] = w.registrar
    except Exception:
        pass
    return info


def resolve_ip(hostname: str) -> str | None:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None
