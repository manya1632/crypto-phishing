"""Security testing module - evaluates robustness against evasion."""

from src.url_analyzer import extract_url_features
from src.crypto_verifier import extract_ssl_features, verify_certificate_chain


SECURITY_TEST_URLS = [
    {"url": "http://192.168.1.1/login.php", "type": "IP-based phishing"},
    {"url": "http://g00gle-secure.com/signin", "type": "Homograph/typosquatting"},
    {"url": "https://bit.ly/3xFake", "type": "URL shortener"},
    {"url": "http://login.paypa1.com.evil.com/verify", "type": "Subdomain spoofing"},
    {"url": "http://example.com@malicious.com", "type": "@ symbol obfuscation"},
    {"url": "https://www.google.com", "type": "Legitimate (control)"},
    {"url": "https://github.com", "type": "Legitimate (control)"},
]


def run_security_tests():
    print("=" * 60)
    print("Security Verification Tests")
    print("=" * 60)

    for test in SECURITY_TEST_URLS:
        url = test["url"]
        attack_type = test["type"]
        print(f"\n--- {attack_type} ---")
        print(f"URL: {url}")

        features = extract_url_features(url)
        flags = []
        if features["has_ip_address"]:
            flags.append("IP address in URL")
        if features["num_at_symbols"] > 0:
            flags.append("@ symbol in URL")
        if features["is_shortened"]:
            flags.append("URL shortener")
        if features["has_suspicious_words"]:
            flags.append("Suspicious keywords")
        if features["num_subdomains"] > 2:
            flags.append("Excessive subdomains")
        if not features["has_https"]:
            flags.append("No HTTPS")

        ssl = extract_ssl_features(url)
        if ssl["has_ssl"] and ssl["is_self_signed"]:
            flags.append("Self-signed certificate")
        if ssl["has_ssl"] and not ssl["cert_valid"]:
            flags.append("Invalid certificate")
        if ssl["has_ssl"] and not ssl["issuer_trusted"]:
            flags.append("Untrusted issuer")

        chain = verify_certificate_chain(url)
        if not chain["chain_valid"] and ssl["has_ssl"]:
            flags.append("Broken certificate chain")

        print(f"  Flags: {flags if flags else 'None'}")
        risk = "HIGH" if len(flags) >= 3 else "MEDIUM" if flags else "LOW"
        print(f"  Risk level: {risk}")


if __name__ == "__main__":
    run_security_tests()
