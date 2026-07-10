import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN (SaaS Mode)
st.set_page_config(
    page_title="Dashboard Performa Terpadu", 
    layout="wide",
    initial_sidebar_state="collapsed" # Menyembunyikan sidebar kiri
)

# 2. FUNGSI AMBIL DATA LIVE DARI GOOGLE SHEETS
@st.cache_data(ttl=600)  # Cache 10 menit agar pembaruan Form cepat muncul
def load_data_from_link():
    sheet_id = "1Uh7sSoiGVQGB9QJWcsNvXIQsZJUXlOA5x_OVxpFCtrA"
    gid_summary = "1761779832"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_summary}"
    
    df = pd.read_csv(url)
    # Membersihkan spasi di awal/akhir nama kolom agar cocok saat dipanggil
    df.columns = df.columns.str.strip()
    
    for col in ['Mismatch_RF', 'Mismatch_GWR', 'Mismatch_OLS']:
        if col in df.columns:
            df[col] = df[col].fillna('Match')
    return df

try:
    df = load_data_from_link()
    
    # Variabel Kolom Kunci Kuantitatif
    col_actual = "Omzet_Actual"
    col_pred_rf = "Prediksi_Omzet_RF"
    col_mismatch = "Mismatch_RF"
    
    st.title("📊 Platform Audit & Performa Cabang")
    st.caption("Aplikasi Analisis Data Terpadu — Riset & Prediksi Multi-Model 2026")
    
    # NAVIGATION TABS (Horizontal di Atas)
    tab_executive, tab_deep_dive = st.tabs([
        "📈 Ringkasan Eksekutif", 
        "🔍 Investigasi Deep-Dive Cabang"
    ])
    
    # =========================================================================
    # TAB 1: RINGKASAN EKSEKUTIF
    # =========================================================================
    with tab_executive:
        st.markdown("### Performa Global & Validasi Model")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Omset Aktual", value=f"Rp {df[col_actual].sum():,.0f}")
        with col2:
            st.metric(label="Total Prediksi Model (Random Forest)", value=f"Rp {df[col_pred_rf].sum():,.0f}")
        with col3:
            total_mismatch = len(df[df[col_mismatch] == 'Mismatch'])
            st.metric(label="Cabang Mismatch Terdeteksi (RF) 🚨", value=total_mismatch)
            
        st.markdown("---")
        
        st.subheader("Scatter Plot Grafik Mismatch: Realisasi vs Prediksi")
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
        
        st.markdown("---")
        st.subheader("Database Terpadu Master (Live Stream)")
        st.dataframe(df, use_container_width=True)

    # =========================================================================
    # TAB 2: INVESTIGASI DEEP-DIVE CABANG
    # =========================================================================
    with tab_deep_dive:
        st.markdown("### Lembar Kerja Audit Lapangan per Cabang")
        
        # Filter Horizontal
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            status_mismatch = st.selectbox("Saring Status:", ["Semua Cabang", "Hanya Mismatch RF"])
        
        if status_mismatch == "Hanya Mismatch RF":
            list_cabang = df[df['Mismatch_RF'] == 'Mismatch']['Nama Cabang'].tolist()
        else:
            list_cabang = df['Nama Cabang'].tolist()
            
        with col_f2:
            if not list_cabang:
                st.warning("Tidak ada cabang yang cocok dengan filter.")
                pilihan_cabang = None
            else:
                pilihan_cabang = st.selectbox("Pilih Target Cabang untuk Di-audit:", list_cabang)
        
        if pilihan_cabang:
            row = df[df['Nama Cabang'] == pilihan_cabang].iloc[0]
            
            st.markdown(f"#### 🏢 Profil Target: **{row['Nama Cabang']}** ({row['Kabupaten']})")
            
            # Mini Metrics
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric(label="Omzet Actual", value=f"Rp {row['Omzet_Actual']:,}")
            with col_m2:
                st.metric(label="Prediksi Model RF", value=f"Rp {row['Prediksi_Omzet_RF']:,}")
            with col_m3:
                st.metric(label="Premium Spot Score", value=f"{row['premium_spot_score']}/100")
            with col_m4:
                if row['Mismatch_RF'] == 'Mismatch':
                    st.error(f"Status: {row['Mismatch_RF']}")
                else:
                    st.success(f"Status: {row['Mismatch_RF']}")
                    
            st.markdown("---")
            
            # Komparasi Fitur Model vs Lapangan
            col_left, col_right = st.columns(2)
            
            # SISI KIRI: INDIKATOR MODEL (KUANTITATIF)
            with col_left:
                st.info("🤖 **Kondisi Fitur Model (Sisi Kuantitatif)**")
                
                with st.container(border=True):
                    st.markdown("##### 📊 Demografi & Wilayah")
                    st.write(f"- **Kategori Wilayah (Mapped):** {row.get('kategori_wilayah_mapped', '-')}")
                    st.write(f"- **Tipe Jalan (Mapped):** {row.get('jalan_mapped', '-')}")
                    st.write(f"- **Total Penduduk Sekitar:** {row.get('penduduk', 0):,} Jiwa")
                    st.write(f"- **Proporsi Usia Produktif:** {row.get('proporsi_usia_produktif', 0) * 100:.1f}%")
                    st.write(f"- **Tingkat Kemiskinan:** {row.get('kemiskinan', '-')}")
                    st.write(f"- **UMK Wilayah:** Rp {row.get('umk', 0):,}")
                    
                with st.container(border=True):
                    st.markdown("##### 🛒 Komersial & Infrastruktur Spasial")
                    st.write(f"- **Lebar Ruko:** {row.get('lebar_ruko', '-')} Meter")
                    st.write(f"- **Commercial Hub Index:** {row.get('commercial_hub_index', '-')}")
                    st.write(f"- **Jumlah Kompetitor Spasial:** {row.get('jumlah_kompetitor', '-')}")
                    st.write(f"- **Fasilitas Belanja:** {row.get('jumlah_fasilitas_belanja', '-')}")
                    st.write(f"- **Jumlah Toko Ponsel:** {row.get('jumlah_toko_ponsel', '-')}")
                    st.write(f"- **Jarak ke Pasar Terdekat:** {row.get('jarak_pasar', '-')} Meter")
                    
            # SISI KANAN: JAWABAN REAL LAPANGAN (KUALITATIF - PENYESUAIAN LIVE KEY)
            with col_right:
                st.warning("📋 **Realitas Riil Lapangan (Hasil Form Riset Lapangan)**")
                
                with st.expandable("👥 1. Kendala SDM & Operasional Cabang", expanded=True):
                    st.write(f"**Lama Beroperasi:** {row.get('Sudah beroperasi berapa lama cabang anda?', '-')}")
                    st.write(f"**Nama Kanit:** {row.get('Nama Kanit Cabang', '-')} ({row.get('Jabatan Karyawan', '-')})")
                    st.write(f"**Jumlah Karyawan Aktif:** {row.get('Jumlah Karyawan Cabang Aktif Saat Ini', '-')}")
                    st.write(f"**Kendala Utama SDM:** {row.get('Kendala utama terkait pengelolaan SDM di cabang saat ini', '-')}")
                    st.write(f"**Waktu Transaksi:** {row.get('Rata-rata waktu satu kali transaksi (menit) ?', '-')} Menit")
                    st.write(f"**Kendala Hambatan Taksiran:** {row.get('Kendala utama yang memperlambat proses taksiran ?', '-')}")

                with st.expandable("📍 2. Aksesibilitas Ruko & Kondisi Fisik"):
                    st.write(f"**Keterlihatan Ruko dari Jalan:** {row.get('Seberapa mudah kantor cabang terlihat dari jalan raya?', '-')}")
                    st.write(f"**Arah Hadap Bangunan:** {row.get('Arah hadap bangunan cabang', '-')}")
                    st.write(f"**Kondisi Papan Nama/Branding:** {row.get('Kondisi papan nama / branding cabang', '-')}")
                    st.write(f"**Kondisi Parkir Depan Cabang:** {row.get('Kondisi parkir di depan cabang — mudah/sulit, berbayar/gratis?', '-')}")
                    st.write(f"**Isu Banjir / Akses Musiman:** {row.get('Apakah lokasi sering banjir atau ada kendala akses musiman?', '-')}")

                with st.expandable("⚔️ 3. Dinamika Persaingan & Pasar Bebas"):
                    st.write(f"**Jumlah Kompetitor Pengamatan Lapangan:** {row.get('Berapa jumlah kompetitor dalam radius 500 m ?', '-')}")
                    st.write(f"**Nama-Nama Kompetitor:** {row.get('Jika ada kompetitor, sebutkan namanya', '-')}")
                    st.write(f"**Dampak Persaingan Terberat:** {row.get('Kompetitor yang paling dirasakan dampak persaingannya? (pegadaian swasta, koperasi simpan pinjam, bpr, rentenir, dll)', '-')}")
                    st.error(f"**🚨 Kompetitor Baru (3 Bulan Terakhir):** {row.get('Kompetitor baru yang muncul belakangan ini atau akhir-akhir ini (3 bulan terakhir). Nama & lokasi?', '-')}")
                    st.write(f"**Alasan Nasabah Pilih Kompetitor:** {row.get('Alasan utama nasabah memilih kompetitor dibanding kita (jika ada)', '-')}")

                with st.expandable("📈 4. Karakteristik Nasabah & Pola Musiman"):
                    st.write(f"**Tipe Nasabah Dominan:** {row.get('Tipe nasabah yang paling dominan?', '-')}")
                    st.write(f"**Estimasi KK dalam Radius 500m:** {row.get('Perkiraan jumlah KK yang tinggal dalam radius 500 m cabang', '-')}")
                    st.write(f"**Detail Pola Musiman Omset:** {row.get('Ceritakan detail pola musiman yang dirasakan karyawan', '-')}")
            
            # BAGIAN BAWAH: REKOMENDASI STRATEGIS TIM CABANG
            st.markdown("---")
            st.subheader("💡 Saran, Kendala Kritis & Rekomendasi Strategis Tim Cabang 2026")
            st.success(f"\"{row.get('Tuliskan saran, kendala kritis, atau rekomendasi strategis lainnya dari tim cabang untuk optimalisasi performa bisnis 2026', '-')}\"")

except Exception as e:
    st.error(f"Gagal memuat sistem dashboard dari link Google Sheets. Pesan Error: {e}")
