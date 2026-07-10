import streamlit as st

st.set_page_config(page_title="Feedback Loop", layout="wide")
st.title("💻 Feedback Loop & Data Scientist Corner")
st.markdown("---")

st.subheader("💡 Validasi Validitas Fitur Model Berdasarkan Hasil Riset")

st.markdown("""
### 1. Matrix Fitur Bermasalah (*Feature Validity*)
*   **`lebar_ruko` & `jumlah_bangunan`**: Seringkali tidak valid jika di lapangan terdapat variabel pengganggu berupa isu aksesibilitas (jalan diperbaiki / parkir liar).
*   **`jumlah_kompetitor`**: Kurang akurat jika hanya menghitung kuantitas statis tanpa memasukkan bobot *agresivitas promo* kompetitor tersebut.

### 2. Rekomendasi Fitur Baru (Feature Engineering untuk Model V2)
Berdasarkan keluhan yang paling sering muncul di Google Form Riset Cabang, tim Data Scientist direkomendasikan menambahkan 2 fitur baru ini di model berikutnya:
1.  `skor_aksesibilitas_jalan` (Skala 1-5, diupdate berkala via form lapangan).
2.  `indikator_promo_kompetitor` (Boolean: True/False).
""")

st.success("🎯 **Target Kerja Sama:** Mengintegrasikan data kualitatif form ini menjadi komponen penimbang (*weighting factor*) pada model prediksi numerik selanjutnya.")
