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

---

## ⚙️ Proses Konversi Data Backend

Sebelum data dapat digunakan untuk prediksi oleh Flask API, backend harus melakukan konversi dari data mentah ke format yang sesuai. Berdasarkan query SQL berikut:

```sql
SELECT
  djc.user_id,
  COUNT(djc.journey_id)                             AS module_count,
  SUM(djc.study_duration)                           AS total_study_duration,
  AVG(djc.study_duration)                           AS avg_study_per_module,
  AVG(djc.study_duration::float / dj.duration)      AS avg_completion_ratio,
  AVG(djc.avg_submission_rating)                    AS avg_submission_rating
FROM "DeveloperJourneyCompletion" djc
JOIN "DeveloperJourney" dj
  ON djc.journey_id = dj.id
GROUP BY djc.user_id
ORDER BY djc.user_id;
```

### 🧠 Tujuan Query (Dalam Bahasa Manusia)

Query ini bertujuan untuk **mengubah data mentah per modul (journey) menjadi ringkasan perilaku belajar per user**, yang kemudian dipakai sebagai input model Machine Learning.

**Transformasi data:**

- **Sebelum:** 1 baris = 1 user untuk 1 modul
- **Sesudah:** 1 baris = 1 user (ringkasan semua modul)

---

### 🔢 Contoh Data Mentah

**Tabel DeveloperJourney (Estimasi Ideal)**

| journey_id | modul | duration (menit) |
| ---------- | ----- | ---------------- |
| 1          | Java  | 2400             |
| 2          | CSS   | 1920             |
| 3          | HTML  | 1440             |

**Tabel DeveloperJourneyCompletion (Real Study)**

| user_id | journey_id | study_duration | rating |
| ------- | ---------- | -------------- | ------ |
| 10      | 1          | 2100           | 4.5    |
| 10      | 2          | 1600           | 4.2    |
| 10      | 3          | 1800           | 4.0    |

---

### 📌 Penjelasan Tiap Bagian Query (Matematis)

#### 1️⃣ COUNT(djc.journey_id) AS module_count

**Makna:**  
Berapa modul yang diikuti user

**Formula Matematika:**
```
module_count = n
```
(n = jumlah modul)

**Contoh:**  
User 10 ikut Java, CSS, HTML  
✅ `module_count = 3`

---

#### 2️⃣ SUM(djc.study_duration) AS total_study_duration

**Makna:**  
Total waktu belajar user di semua modul

**Formula Matematika:**
```
total_study_duration = Σ(i=1 to n) dᵢ
```
(dᵢ = durasi modul ke-i)

**Contoh:**  
2100 + 1600 + 1800 = 5500 menit  
✅ `total_study_duration = 5500`

---

#### 3️⃣ AVG(djc.study_duration) AS avg_study_per_module

**Makna:**  
Rata-rata waktu belajar per modul

**Formula Matematika:**
```
avg_study_per_module = (1/n) × Σ(i=1 to n) dᵢ
```

**Contoh:**  
5500 / 3 = 1833.33 menit  
✅ `avg_study_per_module ≈ 1833`

---

#### 4️⃣ AVG(djc.study_duration::float / dj.duration) AS avg_completion_ratio

⚠️ **INI BAGIAN PALING PENTING**

**Makna:**  
Seberapa cepat atau lambat user menyelesaikan modul, dibanding waktu ideal modul tersebut

**Formula Matematika:**
```
completion_ratioᵢ = waktu_belajar_aktualᵢ / estimasi_modulᵢ

avg_completion_ratio = (1/n) × Σ(i=1 to n) completion_ratioᵢ
```

**Contoh perhitungan per modul:**

| Modul | Aktual | Ideal | Rasio |
| ----- | ------ | ----- | ----- |
| Java  | 2100   | 2400  | 0.875 |
| CSS   | 1600   | 1920  | 0.833 |
| HTML  | 1800   | 1440  | 1.250 |

Rata-rata rasio:
```
avg_completion_ratio = (0.875 + 0.833 + 1.250) / 3 = 0.986
```
✅ `avg_completion_ratio ≈ 0.99`

**Interpretasi:**
- **< 1.0** → lebih lambat dari estimasi
- **≈ 1.0** → sesuai estimasi
- **> 1.0** → lebih cepat dari estimasi

---

#### 5️⃣ AVG(djc.avg_submission_rating) AS avg_submission_rating

**Makna:**  
Kualitas hasil belajar user

**Formula Matematika:**
```
avg_submission_rating = (1/n) × Σ(i=1 to n) rᵢ
```
(rᵢ = rating modul ke-i)

**Contoh:**  
(4.5 + 4.2 + 4.0) / 3 = 4.23  
✅ `avg_submission_rating ≈ 4.23`

---

### 🧠 Kesimpulan Agregasi untuk 1 User

Dari data mentah di atas, hasil agregasi untuk User 10:

| Parameter             | Nilai |
| --------------------- | ----- |
| module_count          | 3     |
| total_study_duration  | 5500  |
| avg_study_per_module  | 1833  |
| avg_completion_ratio  | 0.99  |
| avg_submission_rating | 4.23  |

➡️ **INI 1 BARIS INPUT MODEL ML**

---

### ✅ Hubungan ke Label Gaya Belajar

```python
if avg_completion_ratio >= 1.10:
    Fast Learner
elif avg_completion_ratio >= 0.85:
    Reflective
else:
    Consistent
```

**Untuk contoh di atas:**  
0.99 → **Reflective Learner** ✅

---

### 📋 Tugas Backend

Backend perlu:

1. Mengambil data dari tabel `DeveloperJourneyCompletion` dan `DeveloperJourney`
2. Menghitung agregasi per `user_id` sesuai dengan kolom-kolom yang diminta
3. Mengirim data dalam format JSON seperti yang telah dijelaskan di atas

---

## 📐 Aturan Klasifikasi Gaya Belajar (IMPLEMENTASI SEBENARNYA)

Berdasarkan kode implementasi sebenarnya dalam file `training_model_gaya_belajar_per_modul.py`, aturan klasifikasi adalah sebagai berikut:

### 🔹 Kode Aturan Asli

```python
def label_gaya_belajar(row):
    if row["avg_completion_ratio"] >= 1.1:
        return "Fast Learner"
    elif row["avg_completion_ratio"] >= 0.85:
        return "Reflective"
    else:
        return "Consistent"
```

---

## ✅ 1️⃣ FAST LEARNER — Penjelasan & Perhitungan

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

---

## ✅ 2️⃣ REFLECTIVE LEARNER — Penjelasan & Perhitungan

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

---

## ✅ 3️⃣ CONSISTENT LEARNER — Penjelasan & Perhitungan

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

---

## 🎓 Peran Rating Submission

Field `avg_submission_rating` TIDAK menentukan gaya belajar secara langsung, namun digunakan untuk:

- Rekomendasi belajar
- Insight tambahan
- Evaluasi kualitas pemahaman

---

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

---

## ✅ Kesimpulan

- Sistem menggunakan pendekatan rule-based ML yang explainable
- Klasifikasi didasarkan pada rasio penyelesaian modul dibanding estimasi
- Cocok untuk pembelajaran jangka menengah-panjang
- Mudah diintegrasikan ke REST API
- Mudah dijelaskan secara akademik
