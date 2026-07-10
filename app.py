import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="Executive Performance Dashboard", layout="wide")

st.title("📊 Executive Performance & Model Audit")
st.markdown("---")

# Mock Data (Nanti diganti dengan load data_omset.csv Anda)
data = pd.DataFrame({
    'Nama Cabang': ['MDN001', 'KNG014', 'SMN001', 'PTI001', 'MDN004'],
    'Wilayah': ['Sumatra', 'Jawa Barat', 'Jawa Tengah', 'Jawa Tengah', 'Sumatra'],
    'Actual_Omset': [120, 90, 150, 85, 190],
    'Predicted_Omset': [200, 95, 145, 130, 185]
})
data['Selisih'] = data['Actual_Omset'] - data['Predicted_Omset']

# --- SECTION 1: KPI Cards ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Actual Omset", value=f"{data['Actual_Omset'].sum()}M")
with col2:
    st.metric(label="Total Predicted Omset", value=f"{data['Predicted_Omset'].sum()}M")
with col3:
    total_overpredicted = len(data[data['Selisih'] < -10])
    st.metric(label="Cabang Over-Predicted (🚨)", value=total_overpredicted)

st.markdown("---")

# --- SECTION 2: Visualisasi ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Scatter Plot: Sebaran Deviasi Cabang")
    fig_scatter = px.scatter(data, x="Predicted_Omset", y="Actual_Omset", 
                             hover_name="Nama Cabang", text="Nama Cabang",
                             labels={"Predicted_Omset": "Prediksi", "Actual_Omset": "Aktual"})
    # Tambah garis diagonal target
    fig_scatter.add_shape(type="line", x0=0, y0=0, x1=200, y1=200, line=dict(color="Red", dash="dash"))
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("Top Gap Negatif Terbesar (Over-Predicted)")
    gap_data = data.sort_values(by="Selisih").head(5)
    fig_bar = px.bar(gap_data, x="Nama Cabang", y="Selisih", color="Wilayah",
                     title="Prediksi Terlalu Tinggi vs Aktual")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- SECTION 3: Tabel Kontrol ---
st.markdown("---")
st.subheader("Daftar Detail Performa Cabang")
st.dataframe(data, use_container_width=True)
