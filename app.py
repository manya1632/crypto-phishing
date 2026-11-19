"""Flask web app for phishing URL detection."""

from flask import Flask, render_template, request, jsonify
from src.predictor import PhishingPredictor
from src.url_analyzer import extract_url_features
from src.crypto_verifier import extract_ssl_features, verify_certificate_chain

app = Flask(__name__)
predictor = None


def get_predictor():
    global predictor
    if predictor is None:
        predictor = PhishingPredictor("RandomForest")
    return predictor


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("url") or request.json.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        pred = get_predictor()
        result = pred.predict(url)
        ssl_info = extract_ssl_features(url)
        chain_info = verify_certificate_chain(url)
        result["ssl"] = ssl_info
        result["chain"] = chain_info
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.json
    if not data or "url" not in data:
        return jsonify({"error": "JSON body with 'url' field required"}), 400
    pred = get_predictor()
    return jsonify(pred.predict(data["url"]))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
