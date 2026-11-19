"""SSL/TLS certificate analysis and cryptographic verification."""

import ssl
import socket
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from OpenSSL import crypto
import config


def get_ssl_certificate(url: str) -> dict | None:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname
    port = parsed.port or 443
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as sock:
            sock.settimeout(config.SSL_TIMEOUT)
            sock.connect((hostname, port))
            cert = sock.getpeercert()
            der = sock.getpeercert(binary_form=True)
        return {"parsed": cert, "der": der}
    except Exception:
        return None


def extract_ssl_features(url: str) -> dict:
    features = {
        "has_ssl": 0,
        "cert_valid": 0,
        "cert_days_remaining": -1,
        "cert_age_days": -1,
        "issuer_trusted": 0,
        "cert_key_length": -1,
        "san_count": 0,
        "is_self_signed": 0,
        "signature_algorithm": "unknown",
    }

    cert_data = get_ssl_certificate(url)
    if not cert_data:
        return features

    features["has_ssl"] = 1
    cert = cert_data["parsed"]
    der = cert_data["der"]

    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
    not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
    now = datetime.utcnow()

    features["cert_valid"] = int(not_before <= now <= not_after)
    features["cert_days_remaining"] = (not_after - now).days
    features["cert_age_days"] = (now - not_before).days

    issuer = dict(x[0] for x in cert.get("issuer", ()))
    subject = dict(x[0] for x in cert.get("subject", ()))

    TRUSTED_ISSUERS = [
        "Let's Encrypt", "DigiCert", "Comodo", "GlobalSign",
        "GeoTrust", "Symantec", "Sectigo", "Amazon", "Google Trust Services",
    ]
    issuer_org = issuer.get("organizationName", "")
    features["issuer_trusted"] = int(any(t.lower() in issuer_org.lower() for t in TRUSTED_ISSUERS))
    features["is_self_signed"] = int(issuer == subject)

    san = cert.get("subjectAltName", ())
    features["san_count"] = len(san)

    x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, der)
    pub_key = x509.get_pubkey()
    features["cert_key_length"] = pub_key.bits()
    features["signature_algorithm"] = x509.get_signature_algorithm().decode("utf-8", errors="replace")

    return features


def compute_cert_fingerprint(der_bytes: bytes) -> dict:
    return {
        "sha256": hashlib.sha256(der_bytes).hexdigest(),
        "sha1": hashlib.sha1(der_bytes).hexdigest(),
    }


def verify_certificate_chain(url: str) -> dict:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname
    port = parsed.port or 443
    result = {"chain_valid": False, "chain_length": 0, "error": None}
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as sock:
            sock.settimeout(config.SSL_TIMEOUT)
            sock.connect((hostname, port))
            chain = sock.getpeercert(binary_form=True)
            result["chain_valid"] = True
            result["chain_length"] = 1
    except ssl.SSLCertVerificationError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result
