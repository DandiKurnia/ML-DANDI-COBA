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
    "Fast Learner": {
        "deskripsi": "Kamu cepat memahami konsep baru dan belajar dengan efisien.",
        "saran": [
            "Ambil tantangan coding level Advanced agar tidak bosan setelah menyelesaikan modul.",
            "Luangkan waktu untuk meninjau detail kecil yang mungkin terlewat karena proses belajar yang cepat.",
            "Gunakan sesi belajar singkat sekitar 25 menit untuk menjaga fokus dan konsentrasi."
        ]
    },
    "Reflective": {
        "deskripsi": "Kamu membutuhkan waktu untuk merenung agar paham secara mendalam. Kualitas adalah kekuatanmu.",
        "saran": [
            "Jangan terburu-buru, pastikan kamu memahami konsep sampai benar-benar jelas.",
            "Cobalah menulis rangkuman singkat dari materi yang dipelajari untuk mengecek pemahaman.",
            "Diskusikan materi di forum atau dengan teman untuk mendapatkan perspektif baru."
        ]
    },
    "Consistent": {
        "deskripsi": "Kamu disiplin dan memiliki ritme belajar yang stabil dan teratur.",
        "saran": [
            "Pertahankan ritme belajarmu karena konsistensi adalah kekuatan utama.",
            "Tambahkan durasi belajar sekitar 10 menit secara bertahap untuk meningkatkan kapasitas belajar.",
            "Sesekali eksplorasi topik baru agar rutinitas belajar tetap terasa segar dan menarik."
        ]
    }
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
        data_list = request.get_json()

        # Validasi bahwa data adalah list
        if not isinstance(data_list, list):
            return jsonify({"error": "Expected a list of user data"}), 400

        results = []

        for idx, data in enumerate(data_list):
            # Validasi tiap field dalam FEATURES
            for f in FEATURES:
                if f not in data:
                    return jsonify({"error": f"Item {idx}: {f} is required"}), 400

            # Buat DataFrame dan lakukan prediksi
            df = pd.DataFrame([data])[FEATURES]
            prediction = model.predict(df)[0]
            insight = INSIGHTS.get(prediction, {})

            results.append({
                "user_id": data.get("user_id"),
                "gaya_belajar": prediction,
                "deskripsi": insight.get("deskripsi", ""),
                "saran": insight.get("saran", [])
            })

        return jsonify(results), 200

    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
