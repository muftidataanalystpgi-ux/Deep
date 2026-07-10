import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Executive Performance Dashboard", layout="wide")
st.title("Multi-Model Performance & Audit Mismatch")
st.markdown("---")

# 1. Load Data dengan Pembersihan Nama Kolom
@st.cache_data
def load_data():
    # Ganti dengan path file CSV asli Anda
    df = pd.read_csv('data/data_omset.csv') 
    
    # Kunci Keamanan 1: Hilangkan spasi tak terlihat di nama kolom
    df.columns = df.columns.str.strip()
    
    # Kunci Keamanan 2: Isi nilai kosong pada kolom Mismatch agar Plotly tidak error
    if 'Mismatch_RF' in df.columns:
        df['Mismatch_RF'] = df['Mismatch_RF'].fillna('Unknown')
        
    return df

try:
    df = load_data()

    # --- SINKRONISASI NAMA KOLOM ---
    # Definisikan nama kolom sesuai data Anda (pastikan huruf besar/kecilnya sama)
    col_x = "Prediksi_Omset_RF"  # Sesuai list Anda sebelumnya
    col_y = "Omzet_Actual"       # Sesuai list Anda sebelumnya
    col_color = "Mismatch_RF"

    # Validasi apakah kolom benar-benar ada di CSV
    missing_cols = [c for c in [col_x, col_y, col_color] if c not in df.columns]
    
    if missing_cols:
        st.error(f"Kolom berikut tidak ditemukan di CSV Anda: {missing_cols}")
        st.info(f"Kolom yang tersedia di file Anda adalah: {list(df.columns)}")
    else:
        # --- SECTION 1: KPI Cards ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Actual Omset", value=f"{df[col_y].sum():,.0f}")
        with col2:
            st.metric(label="Total Prediksi Omset (RF)", value=f"{df[col_x].sum():,.0f}")
        with col3:
            total_mismatch = len(df[df[col_color] == 'Mismatch'])
            st.metric(label="Total Cabang Mismatch (RF)", value=total_mismatch)

        st.markdown("---")

        # --- SECTION 2: Visualisasi ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Scatter Plot: Aktual vs Prediksi Random Forest")
            
            # Pengaman warna map jika ada data selain Match/Mismatch
            color_map = {'Mismatch': '#EF553B', 'Match': '#636EFA', 'Unknown': '#A3A3A3'}
            
            fig_scatter = px.scatter(
                df, 
                x=col_x, 
                y=col_y, 
                color=col_color, 
                hover_name="nama_cabang", 
                text="nama_cabang",
                color_discrete_map=color_map,
                labels={col_x: "Prediksi Random Forest", col_y: "Aktual"}
            )
            
            # Buat garis diagonal dinamis mengikuti nilai maksimum data
            max_val = max(df[col_x].max(), df[col_y].max())
            fig_scatter.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="Gray", dash="dash"))
            
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_right:
            st.subheader("Distribusi Cabang Mismatch per Kategori Wilayah")
            if 'kategori_wilayah' in df.columns:
                fig_bar = px.histogram(df, x="kategori_wilayah", color=col_color, barmode="group", color_discrete_map=color_map)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.caption("Kolom 'kategori_wilayah' tidak ditemukan untuk grafik batangan.")

        # --- SECTION 3: Tabel ---
        st.markdown("---")
        st.subheader("Daftar Detail Performa Cabang")
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Gagal membaca file data. Pastikan file berada di folder yang benar. Error: {e}")
