import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Performa Terpadu", layout="wide")
st.title("Dashboard Audit Performa Cabang & Mismatch Model")
st.markdown("---")

# Fungsi untuk Menarik Data Live dari Google Sheets
@st.cache_data(ttl=3600)  # Cache disimpan selama 1 jam agar loading cepat
def load_data_from_link():
    # ID Spreadsheet dan GID Sheet 'summary' sesuai link Anda
    sheet_id = "1Uh7sSoiGVQGB9QJWcsNvXIQsZJUXlOA5x_OVxpFCtrA"
    gid_summary = "1761779832"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_summary}"
    
    # Membaca data langsung via URL internet
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()  # Bersihkan spasi gaib pada nama kolom
    
    # Isi nilai kosong pada kolom flag Mismatch agar tidak error saat divisualisasikan
    for col in ['Mismatch_RF', 'Mismatch_GWR', 'Mismatch_OLS']:
        if col in df.columns:
            df[col] = df[col].fillna('Match')
    return df

try:
    # Load Database Utama
    df = load_data_from_link()
    
    # --- DEKLARASI VARIABEL UTAMA ---
    col_actual = "Omzet_Actual"
    col_pred_rf = "Prediksi_Omzet_RF"
    col_mismatch = "Mismatch_RF"
    
    if col_actual in df.columns and col_pred_rf in df.columns:
        
        # --- SECTION 1: RINGKASAN EKSEKUTIF (KPI CARDS) ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Omset Aktual", value=f"Rp {df[col_actual].sum():,.0f}")
        with col2:
            st.metric(label="Total Prediksi Model (Random Forest)", value=f"Rp {df[col_pred_rf].sum():,.0f}")
        with col3:
            total_mismatch = len(df[df[col_mismatch] == 'Mismatch'])
            st.metric(label="Cabang Mismatch Terdeteksi (RF) 🚨", value=total_mismatch)
            
        st.markdown("---")
        
        # --- SECTION 2: SCATTER PLOT AUDIT ---
        st.subheader("Scatter Plot Audit: Realisasi vs Prediksi")
        fig = px.scatter(
            df, 
            x=col_pred_rf, 
            y=col_actual, 
            color=col_mismatch,
            hover_name="Nama Cabang",
            labels={col_pred_rf: "Prediksi Omzet RF", col_actual: "Omzet Aktual"},
            color_discrete_map={'Mismatch': '#EF553B', 'Match': '#636EFA'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- SECTION 3: PRATINJAU DATA MASTER ---
        st.markdown("---")
        st.subheader("Database Terpadu (Live Terhubung ke Google Sheets)")
        st.dataframe(df, use_container_width=True)
        
    else:
        st.warning("Data berhasil dimuat, namun kolom 'Omzet_Actual' atau 'Prediksi_Omzet_RF' tidak ditemukan.")

except Exception as e:
    st.error(f"Gagal menarik data secara live dari Google Sheets. Pastikan akses link diatur ke 'Anyone with the link can view'. Error: {e}")
