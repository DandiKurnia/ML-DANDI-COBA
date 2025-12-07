from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

# ======================
# LOAD MODEL (ONCE)
# ======================
MODEL_PATH = "model_gaya_belajar.pkl"
model = joblib.load(MODEL_PATH)

FEATURES = [
    "module_count",
    "total_study_duration",
    "avg_study_per_module",
    "avg_completion_ratio",
    "avg_submission_rating"
]

INSIGHTS = {
    "Fast Learner": "Menyerap materi lebih cepat dari estimasi modul.",
    "Reflective": "Belajar stabil dan mendalam sesuai estimasi modul.",
    "Consistent": "Belajar konsisten namun membutuhkan waktu lebih lama."
}

# ======================
# HEALTH CHECK
# ======================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "loaded"}), 200

# ======================
# PREDICTION ENDPOINT
# ======================
@app.route("/predict-gaya-belajar", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        # ✅ pastikan semua fitur ada
        for f in FEATURES:
            if f not in data:
                return jsonify({"error": f"{f} is required"}), 400

        df = pd.DataFrame([data])[FEATURES]

        prediction = model.predict(df)[0]

        return jsonify({
            "gaya_belajar": prediction,
            "insight": INSIGHTS.get(prediction, "")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
