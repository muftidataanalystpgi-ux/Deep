import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Executive Performance Dashboard", layout="wide")
st.title("Multi-Model Performance & Audit Mismatch")
st.markdown("---")

# 1. Load Data Riil (Pastikan file diletakkan di folder data/data_omset.csv)
@st.cache_data
def load_data():
    # Ganti dengan path riil Anda, contoh: pd.read_csv('data/data_omset.csv')
    # Di bawah ini adalah mock dataframe dengan struktur kolom persis seperti milik Anda
    mock_data = pd.DataFrame({
        'nama_cabang': ['MDN001', 'KNG014', 'PTI001', 'MGW007', 'UNR006'],
        'kategori_wilayah': ['Ritel Padat', 'Suburban', 'Sentra Dagang', 'Ritel Padat', 'Suburban'],
        'Omzet_Actual': [120, 90, 85, 210, 140],
        'Prediksi_Omzet_RF': [200, 95, 130, 215, 110],
        'Prediksi_Omzet_GWR': [180, 92, 125, 230, 115],
        'Mismatch_RF': ['Mismatch', 'Match', 'Mismatch', 'Match', 'Match'],
        'commercial_hub_index': [0.85, 0.42, 0.61, 0.92, 0.55]
    })
    return mock_data

df = load_data()

# --- SECTION 1: KPI Cards (Fokus ke Model Random Forest sebagai contoh) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Actual Omset", value=f"{df['Omzet_Actual'].sum()}M")
with col2:
    st.metric(label="Total Prediksi Omset (RF)", value=f"{df['Prediksi_Omzet_RF'].sum()}M")
with col3:
    total_mismatch_rf = len(df[df['Mismatch_RF'] == 'Mismatch'])
    st.metric(label="Total Cabang Mismatch (RF) 🚨", value=total_mismatch_rf)
with col4:
    avg_hub_index = round(df['commercial_hub_index'].mean(), 2)
    st.metric(label="Rata-rata Hub Index", value=avg_hub_index)

st.markdown("---")

# --- SECTION 2: Visualisasi Komparasi Model ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Scatter Plot: Aktual vs Prediksi Random Forest")
    fig_scatter = px.scatter(df, x="Prediksi_Omset_RF", y="Omzet_Actual", 
                             color="Mismatch_RF", hover_name="nama_cabang", text="nama_cabang",
                             color_discrete_map={'Mismatch': '#EF553B', 'Match': '#636EFA'},
                             labels={"Prediksi_Omset_RF": "Prediksi Random Forest", "Omzet_Actual": "Aktual"})
    fig_scatter.add_shape(type="line", x0=0, y0=0, x1=250, y1=250, line=dict(color="Gray", dash="dash"))
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("Distribusi Cabang Mismatch per Kategori Wilayah")
    fig_bar = px.histogram(df, x="kategori_wilayah", color="Mismatch_RF", barmode="group",
                           color_discrete_map={'Mismatch': '#EF553B', 'Match': '#636EFA'})
    st.plotly_chart(fig_bar, use_container_width=True)

# --- SECTION 3: Data Table Filtered by Mismatch ---
st.markdown("---")
st.subheader("Daftar Cabang yang Mengalami Mismatch (Prediksi vs Realitas Lapangan)")
show_mismatch_only = st.checkbox("Tampilkan Hanya Cabang Mismatch")

if show_mismatch_only:
    st.dataframe(df[df['Mismatch_RF'] == 'Mismatch'], use_container_width=True)
else:
    st.dataframe(df, use_container_width=True)
