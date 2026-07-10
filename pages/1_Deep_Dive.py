import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Deep-Dive Analisis", layout="wide")
st.title("🔍 Deep-Dive Lapangan & Analisis Akar Masalah")

# Mock Data Gabungan Model & Form Riset
cabang_detail = {
    'MDN001': {
        'UMK': 'Tinggi (Rp 4.5M)', 'Penduduk': 'Padat', 'Kompetitor_Model': 1,
        'Kendala_Form': 'Akses jalan di depan ruko ditutup total karena proyek perbaikan saluran air kota semenjak awal bulan. Konsumen kesulitan parkir.',
        'Kompetitor_Form': '1 Kompetitor agresif melakukan predatory pricing (diskon 50%) semenjak minggu ke-2.'
    },
    'KNG014': {
        'UMK': 'Sedang (Rp 3.1M)', 'Penduduk': 'Sedang', 'Kompetitor_Model': 2,
        'Kendala_Form': 'Stok barang inti sering kosong karena keterlambatan pengiriman dari gudang pusat.',
        'Kompetitor_Form': 'Kompetitor normal, tidak ada pergerakan agresif.'
    }
}

# --- PANEL FILTER ---
st.sidebar.header("Filter Analisis")
pilihan_cabang = st.sidebar.selectbox("Pilih Nama Cabang:", list(cabang_detail.keys()))

st.markdown(f"### Analisis Audit untuk Cabang: **{pilihan_cabang}**")

# --- SIDE-BY-SIDE COMPARISON ---
col_model, col_lapangan = st.columns(2)

with col_model:
    st.info("🤖 **Sisi Kiri: Profil Variabel Model (Kenapa Prediksi Tinggi?)**")
    st.write(f"- **Faktor UMK:** {cabang_detail[pilihan_cabang]['UMK']}")
    st.write(f"- **Kepadatan Penduduk:** {cabang_detail[pilihan_cabang]['Penduduk']}")
    st.write(f"- **Jumlah Kompetitor (Data Model):** {cabang_detail[pilihan_cabang]['Kompetitor_Model']} kompetitor terdeteksi.")

with col_lapangan:
    st.warning("📋 **Sisi Kanan: Realitas Form Riset (Kenapa Aktual Rendah?)**")
    st.markdown("**Kendala Utama di Lapangan:**")
    st.write(cabang_detail[pilihan_cabang]['Kendala_Form'])
    st.markdown("**Dinamika Kompetitor Riil:**")
    st.write(cabang_detail[pilihan_cabang]['Kompetitor_Form'])

# --- PARETO CHART KENDALA ---
st.markdown("---")
st.subheader("Peta Kendala Nasional (Data Form Responses)")
# Mock data aggregasi kendala
data_kendala = pd.DataFrame({
    'Kategori Kendala': ['Akses Jalan/Parkir', 'Agresivitas Kompetitor', 'Masalah Stok Internal', 'Daya Beli Turun'],
    'Jumlah Cabang': [15, 12, 6, 3]
})
fig_pareto = px.bar(data_kendala, x='Jumlah Cabang', y='Kategori Kendala', orientation='h', color='Kategori Kendala')
st.plotly_chart(fig_pareto, use_container_width=True)
