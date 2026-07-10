import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Performa Terpadu", layout="wide")
st.title("📊 Dashboard Audit Performa Cabang & Mismatch Model")
st.markdown("---")

@st.cache_data(ttl=3600) # Data di-cache selama 1 jam, silakan hapus atau ubah sesuai kebutuhan
def load_data_from_link():
    # URL Spreadsheet Anda (Bagian 'edit' diganti menjadi 'export?format=csv' dan diarahkan ke gid sheet summary)
    sheet_id = "1Uh7sSoiGVQGB9QJWcsNvXIQsZJUXlOA5x_OVxpFCtrA"
    gid_summary = "1761779832"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_summary}"
    
    # Membaca data langsung dari URL Internet
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip() # Bersihkan spasi nama kolom
    
    # Isi nilai kosong pada kolom Mismatch agar tidak error saat di-render Plotly
    if 'Mismatch_RF' in df.columns:
        df['Mismatch_RF'] = df['Mismatch_RF'].fillna('Match')
    return df

try:
    # Mengambil data dari link Google Sheets Anda
    df = load_data_from_link()
    
    # --- DEKLARASI VARIABEL UTAMA ---
    col_actual = "Omzet_Actual"
    col_pred_rf = "Prediksi_Omzet_RF"
    col_mismatch = "Mismatch_RF"
    
    # Menampilkan Informasi jika kolom yang dicari aman
    if col_actual in df.columns and col_pred_rf in df.columns:
        
        # --- SECTION 1: KPI Cards ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Omset Aktual", value=f"Rp {df[col_actual].sum():,.0f}")
        with col2:
            st.metric(label="Total Prediksi Model (Random Forest)", value=f"Rp {df[col_pred_rf].sum():,.0f}")
        with col3:
            total_mismatch = len(df[df[col_mismatch] == 'Mismatch'])
            st.metric(label="Cabang Mismatch Terdeteksi 🚨", value=total_mismatch)
            
        st.markdown("---")
        
        # --- SECTION 2: VISUALISASI SCATTER PLOT ---
        st.subheader("Scatter Plot Audit: Realisasi vs Prediksi")
        fig = px.scatter(
            df, 
            x=col_pred_rf, 
            y=col_actual, 
            color=col_mismatch,
            hover_name="Nama Cabang",
            color_discrete_map={'Mismatch': '#EF553B', 'Match': '#636EFA'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- SECTION 3: DETAIL TABEL MASTER ---
        st.markdown("---")
        st.subheader("Database Terpadu (Live dari Google Sheets)")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Data berhasil dimuat dari link, namun kolom utama seperti Omzet_Actual atau Prediksi_Omzet_RF tidak ditemukan.")
        st.write("Kolom yang terbaca saat ini:", list(df.columns))

except Exception as e:
    st.error(f"Gagal menarik data secara live dari Google Sheets. Pastikan akses link bersifat publik/dapat dilihat. Error: {e}")
