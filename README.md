# 📊 Sistem Analisis Gaya Belajar Siswa (Explainable ML)

Sistem ini menganalisis **aktivitas belajar siswa** berdasarkan data agregasi aktivitas
dalam periode tertentu (misalnya 1 bulan) untuk mengidentifikasi **gaya belajar utama**:

- Fast Learner
- Reflective Learner
- Consistent Learner

Pendekatan yang digunakan adalah **Decision Tree berbasis aturan pedagogik**
agar hasil klasifikasi **mudah dijelaskan, transparan, dan dapat dipertanggungjawabkan**.

---

## 🎯 Ruang Lingkup & Tujuan

Sistem ini dibuat untuk:

- Menganalisis aktivitas belajar siswa (waktu belajar, frekuensi, kecepatan)
- Mengelompokkan siswa ke dalam gaya belajar yang sesuai
- Memberikan insight dan saran belajar yang relevan
- Digunakan dalam aplikasi pembelajaran digital berbasis data

Sistem **tidak menilai kepintaran siswa**, melainkan **pola dan kebiasaan belajar**.

---

## 🧠 Konsep Dasar Sistem

1. Aktivitas belajar siswa dicatat harian
2. Data harian diringkas (agregasi) per periode
3. Sistem melakukan perhitungan dari data agregasi
4. Gaya belajar ditentukan berdasarkan aturan yang jelas
5. Nilai akademik digunakan untuk rekomendasi, bukan klasifikasi utama

---

## 📥 Format Input Data (JSON)

Data dikirim ke REST API dalam format berikut:

```json
{
  "module_count": 15,
  "total_study_duration": 3600,
  "avg_study_per_module": 240,
  "avg_completion_ratio": 1.2,
  "avg_submission_rating": 4.2
}
```

### Penjelasan Field

| Field                 | Deskripsi                            |
| --------------------- | ------------------------------------ |
| module_count          | Jumlah modul yang diselesaikan       |
| total_study_duration  | Total durasi belajar (menit)         |
| avg_study_per_module  | Rata-rata durasi belajar per modul   |
| avg_completion_ratio  | Rasio penyelesaian vs estimasi modul |
| avg_submission_rating | Rata-rata rating tugas               |

## ⚙️ Proses Konversi Data Backend

Sebelum data dapat digunakan untuk prediksi oleh Flask API, backend harus melakukan konversi dari data mentah ke format yang sesuai. Berdasarkan query SQL berikut:

```sql
SELECT
  djc.user_id,
  COUNT(djc.journey_id)                  AS module_count,
  SUM(djc.study_duration)                AS total_study_duration,
  AVG(djc.study_duration)                AS avg_study_per_module,
  AVG(djc.study_duration::float / dj.duration)
                                       AS avg_completion_ratio,
  AVG(djc.avg_submission_rating)         AS avg_submission_rating
FROM "DeveloperJourneyCompletion" djc
JOIN "DeveloperJourney" dj
  ON djc.journey_id = dj.id
GROUP BY djc.user_id
ORDER BY djc.user_id;
```

### 🧮 Perhitungan Matematika avg_completion_ratio

Rasio penyelesaian (`avg_completion_ratio`) dihitung berdasarkan perbandingan antara waktu studi aktual dengan estimasi waktu penyelesaian modul:

```
avg_completion_ratio = rata-rata (study_duration / duration)
```

Dimana:

- `study_duration` = durasi aktual yang dibutuhkan siswa untuk menyelesaikan suatu modul (dalam menit)
- `duration` = estimasi waktu yang seharusnya dibutuhkan untuk menyelesaikan modul (dalam menit)

Contoh perhitungan:
Jika seorang siswa menyelesaikan 3 modul dengan data berikut:

- Modul 1: study_duration = 120 menit, duration = 100 menit → rasio = 120/100 = 1.2
- Modul 2: study_duration = 90 menit, duration = 100 menit → rasio = 90/100 = 0.9
- Modul 3: study_duration = 150 menit, duration = 100 menit → rasio = 150/100 = 1.5

Maka avg_completion_ratio = (1.2 + 0.9 + 1.5) / 3 = 1.2

Interpretasi:

- Jika rasio > 1.0: Siswa menyelesaikan modul lebih cepat dari estimasi
- Jika rasio = 1.0: Siswa menyelesaikan modul sesuai estimasi
- Jika rasio < 1.0: Siswa menyelesaikan modul lebih lambat dari estimasi

Backend perlu:

1. Mengambil data dari tabel DeveloperJourneyCompletion dan DeveloperJourney
2. Menghitung agregasi per user_id sesuai dengan kolom-kolom yang diminta
3. Mengirim data dalam format JSON seperti yang telah dijelaskan di atas

## 📐 Aturan Klasifikasi Gaya Belajar (IMPLEMENTASI SEBENARNYA)

Berdasarkan kode implementasi sebenarnya dalam file `training_model_gaya_belajar_per_modul.py`, aturan klasifikasi adalah sebagai berikut:

### 🔹 KODE ATURAN ASLI

```python
def label_gaya_belajar(row):
    if row["avg_completion_ratio"] >= 1.1:
        return "Fast Learner"
    elif row["avg_completion_ratio"] >= 0.85:
        return "Reflective"
    else:
        return "Consistent"
```

## ✅ 1️⃣ FAST LEARNER — PENJELASAN & PERHITUNGAN

### Definisi

Siswa yang menyelesaikan modul lebih cepat dari estimasi (completion ratio ≥ 1.1).

### Aturan

```
avg_completion_ratio ≥ 1.1
```

### Contoh Data

```json
{
  "module_count": 10,
  "total_study_duration": 1800,
  "avg_study_per_module": 180,
  "avg_completion_ratio": 1.2,
  "avg_submission_rating": 4.0
}
```

### Evaluasi Rule

```
1.2 ≥ 1.1 ✅
```

### ➡️ HASIL: Fast Learner

Fast Learner adalah siswa yang menyelesaikan modul 10% lebih cepat dari estimasi waktu yang diberikan.

## ✅ 2️⃣ REFLECTIVE LEARNER — PENJELASAN & PERHITUNGAN

### Definisi

Siswa yang menyelesaikan modul sesuai dengan estimasi (completion ratio antara 0.85-1.09).

### Aturan

```
avg_completion_ratio ≥ 0.85 DAN avg_completion_ratio < 1.1
```

### Contoh Data

```json
{
  "module_count": 8,
  "total_study_duration": 1600,
  "avg_study_per_module": 200,
  "avg_completion_ratio": 0.95,
  "avg_submission_rating": 4.5
}
```

### Evaluasi Rule

```
0.95 ≥ 0.85 ✅
0.95 < 1.1 ✅
```

### ➡️ HASIL: Reflective Learner

Reflective Learner adalah siswa yang menyelesaikan modul dalam waktu mendekati estimasi, menunjukkan pembelajaran yang stabil dan mendalam.

## ✅ 3️⃣ CONSISTENT LEARNER — PENJELASAN & PERHITUNGAN

### Definisi

Siswa yang menyelesaikan modul lebih lambat dari estimasi (completion ratio < 0.85).

### Aturan

```
avg_completion_ratio < 0.85
```

### Contoh Data

```json
{
  "module_count": 12,
  "total_study_duration": 2400,
  "avg_study_per_module": 200,
  "avg_completion_ratio": 0.75,
  "avg_submission_rating": 3.8
}
```

### Evaluasi Rule

```
0.75 < 0.85 ✅
```

### ➡️ HASIL: Consistent Learner

Consistent Learner adalah siswa yang membutuhkan waktu lebih lama dari estimasi untuk menyelesaikan modul, namun tetap konsisten dalam belajar.

## 🎓 Peran Rating Submission

Field `avg_submission_rating` TIDAK menentukan gaya belajar secara langsung, namun digunakan untuk:

- Rekomendasi belajar
- Insight tambahan
- Evaluasi kualitas pemahaman

## 📤 Output API

```json
{
  "status": "success",
  "gaya_belajar": "Fast Learner",
  "deskripsi": "Menyerap materi lebih cepat dari estimasi modul.",
  "saran": [
    "Ambil tantangan coding level Advanced agar tidak bosan setelah menyelesaikan modul.",
    "Luangkan waktu untuk meninjau detail kecil yang mungkin terlewat karena proses belajar yang cepat.",
    "Gunakan sesi belajar singkat sekitar 25 menit untuk menjaga fokus dan konsentrasi."
  ]
}
```

## ✅ Kesimpulan

- Sistem menggunakan pendekatan rule-based ML yang explainable
- Klasifikasi didasarkan pada rasio penyelesaian modul dibanding estimasi
- Cocok untuk pembelajaran jangka menengah-panjang
- Mudah diintegrasikan ke REST API
- Mudah dijelaskan secara akademik
