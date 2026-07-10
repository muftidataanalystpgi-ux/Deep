import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard Performa Terpadu 2026", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNGSI AMBIL DATA LIVE DARI GOOGLE SHEETS
@st.cache_data(ttl=600)
def load_data_from_link():
    sheet_id = "1Uh7sSoiGVQGB9QJWcsNvXIQsZJUXlOA5x_OVxpFCtrA"
    gid_summary = "1761779832"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_summary}"
    
    df = pd.read_csv(url)
    # Membersihkan spasi di awal/akhir nama kolom agar presisi
    df.columns = df.columns.str.strip()
    
    # Mengisi nilai kosong pada kolom Mismatch
    for col in ['Mismatch_RF', 'Mismatch_GWR', 'Mismatch_OLS']:
        if col in df.columns:
            df[col] = df[col].fillna('Match')
    return df

try:
    df = load_data_from_link()
    
    # Variabel Utama Dashboard
    col_actual = "Omzet_Actual"
    col_pred_rf = "Prediksi_Omzet_RF"
    col_mismatch = "Mismatch_RF"
    
    st.title("📊 Platform Audit & Performa Cabang")
    st.caption("Aplikasi Analisis Data Terpadu — Riset Lapangan & Prediksi Multi-Model 2026")
    
    # NAVIGATION TABS
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
            
            st.markdown(f"#### 🏢 Profil Target: **{row['Nama Cabang']}** ({row.get('Kabupaten', '-')})")
            
            # Mini Metrics Atas
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric(label="Omzet Actual", value=f"Rp {row[col_actual]:,}")
            with col_m2:
                st.metric(label="Prediksi Model RF", value=f"Rp {row[col_pred_rf]:,}")
            with col_m3:
                st.metric(label="Premium Spot Score", value=f"{row.get('premium_spot_score', '-')}/100")
            with col_m4:
                if row[col_mismatch] == 'Mismatch':
                    st.error(f"Status: {row[col_mismatch]}")
                else:
                    st.success(f"Status: {row[col_mismatch]}")
                    
            st.markdown("---")
            
            # Komparasi Fitur Model vs Lapangan
            col_left, col_right = st.columns(2)
            
            # -----------------------------------------------------------------
            # SISI KIRI: INDIKATOR MODEL & DATA DEMOGRAFI (FITUR MODEL)
            # -----------------------------------------------------------------
            with col_left:
                st.info("🤖 **Kondisi Fitur Model (Sisi Kuantitatif & Kewilayahan)**")
                
                with st.container(border=True):
                    st.markdown("##### 📊 Demografi & Makro Wilayah")
                    st.write(f"- **Kabupaten:** {row.get('Kabupaten', '-')}")
                    st.write(f"- **Kategori Wilayah (Model):** {row.get('kategori_wilayah_mapped', row.get('kategori_wilayah', '-'))}")
                    st.write(f"- **Tipe Jalan (Model):** {row.get('jalan_mapped', row.get('tipe_jalan', '-'))}")
                    st.write(f"- **Total Penduduk:** {row.get('penduduk', 0):,} Jiwa")
                    st.write(f"- **Proporsi Usia Produktif:** {row.get('proporsi_usia_produktif', 0) * 100:.1f}%")
                    st.write(f"- **Tingkat Kemiskinan:** {row.get('kemiskinan', '-')}")
                    st.write(f"- **Rasio Pria/Wanita:** {row.get('proporsi_pria', '-')}/{row.get('proporsi_wanita', '-')}")
                    st.write(f"- **UMK Terpeta:** Rp {row.get('umk', 0):,}")
                    
                with st.container(border=True):
                    st.markdown("##### 🛒 Indikator Spasial & Komersial")
                    st.write(f"- **Lebar Ruko:** {row.get('lebar_ruko', '-')} Meter")
                    st.write(f"- **Commercial Hub Index:** {row.get('commercial_hub_index', '-')}")
                    st.write(f"- **Fasilitas Belanja:** {row.get('jumlah_fasilitas_belanja', '-')}")
                    st.write(f"- **Jumlah Toko Ponsel:** {row.get('jumlah_toko_ponsel', '-')}")
                    st.write(f"- **Jumlah Pasar Tradisional:** {row.get('jumlah_pasar_tradisional', '-')}")
                    st.write(f"- **Jarak Ke Pasar Terdekat:** {row.get('jarak_pasar', '-')} Meter")
                    st.write(f"- **Jumlah Restoran:** {row.get('jumlah_restoran', '-')}")
                    st.write(f"- **Jumlah Pusat Perbelanjaan/Swalayan:** {row.get('Jumlah pusat perbelanjaan modern / swalayan / mall dalam radius 250 m?', '-')}")
                    st.write(f"- **Jumlah Kompetitor Spasial:** {row.get('jumlah_kompetitor', '-')}")
                    st.write(f"- **Kepadatan Kompetitor/Populasi:** {row.get('comp_per_pop', '-')}")

                with st.container(border=True):
                    st.markdown("##### 📐 Evaluasi Multi-Model (Prediction Gap)")
                    st.write(f"- **Prediksi OLS:** Rp {row.get('Prediksi_Omzet_OLS', 0):,}")
                    st.write(f"- **Prediksi GWR:** Rp {row.get('Prediksi_Omzet_GWR', 0):,}")
                    st.write(f"- **Klaster Omzet:** {row.get('Klaster_Omzet', '-')}")
                    st.write(f"- **Cabang Terdekat Referensi:** {row.get('Cabang_Terdekat_Ref', '-')} ({row.get('Jarak_Ref_KM', '-')} KM)")

            # -----------------------------------------------------------------
            # SISI KANAN: JAWABAN REAL LAPANGAN (KUALITATIF DARI FORM)
            # -----------------------------------------------------------------
            with col_right:
                st.warning("📋 **Realitas Riil Lapangan (Hasil Form Riset Lapangan)**")
                
                with st.expandable("👥 1. SDM & Operasional Cabang", expanded=True):
                    st.write(f"**Lama Beroperasi:** {row.get('Sudah beroperasi berapa lama cabang anda?', '-')}")
                    st.write(f"**Kategori Class Cabang:** {row.get('Kategori Class Cabang di lokasi anda', '-')}")
                    st.write(f"**Nama Kanit:** {row.get('Nama Kanit Cabang', '-')} ({row.get('Jabatan Karyawan', '-')})")
                    st.write(f"**Lama Bekerja di Cabang:** {row.get('Lama Bekerja di Cabang tersebut', '-')}")
                    st.write(f"**Jumlah Karyawan Aktif:** {row.get('Jumlah Karyawan Cabang Aktif Saat Ini', '-')}")
                    st.write(f"**Absensi (Sering Tidak Masuk?):** {row.get('Apakah sering ada karyawan yang tidak masuk?', '-')}")
                    st.write(f"**Keaktifan Jemput Bola/Promosi:** {row.get('Apakah karyawan aktif promosi /kunjungi / jemput bola nasabah?', '-')}")
                    st.error(f"**Kendala Utama SDM:** {row.get('Kendala utama terkait pengelolaan SDM di cabang saat ini', '-')}")
                    st.write(f"**Waktu Transaksi:** {row.get('Rata-rata waktu satu kali transaksi (menit) ?', '-')} Menit")
                    st.write(f"**Hambatan Taksiran:** {row.get('Kendala utama yang memperlambat proses taksiran ?', '-')}")

                with st.expandable("💰 2. Produk, Plafon & Kebijakan Taksiran"):
                    st.write(f"**Gadai Emas:** {row.get('Gadai Emas', '-')}")
                    st.write(f"**Gadai Elektronik:** {row.get('Gadai Elektronik', '-')}")
                    st.write(f"**Gadai BPKB:** {row.get('Gadai BPKB', '-')}")
                    st.write(f"**Gadai Lain-lain:** {row.get('Gadai lain-lain (sebutkan)', '-')}")
                    st.write(f"**Maksimum Plafon Saat Ini:** {row.get('Nilai taksiran maksimum yang bisa diproses cabang ini (plafon)?', '-')}")
                    st.write(f"**Butuh Kenaikan Plafon?:** {row.get('Apakah cabang membutuhkan kenaikan limit plafon taksiran?', '-')}")
                    st.write(f"**Alasan Penyesuaian Plafon:** {row.get('Jika butuh. Alasan utama kebutuhan penyesuaian plafon taksiran tersebut. Jika tidak butuh isi dengan \"Tidak\" atau \" - \"', '-')}")
                    st.error(f"**Barang Paling Sering Ditolak & Alasan:** {row.get('Jenis barang yang paling sering ditolak dan alasannya?', '-')}")

                with st.expandable("📍 3. Aksesibilitas, Fisik Ruko & Lingkungan"):
                    st.write(f"**Keterlihatan dari Jalan:** {row.get('Seberapa mudah kantor cabang terlihat dari jalan raya?', '-')}")
                    st.write(f"**Arah Hadap Bangunan:** {row.get('Arah hadap bangunan cabang', '-')}")
                    st.write(f"**Kondisi Papan Nama/Branding:** {row.get('Kondisi papan nama / branding cabang', '-')}")
                    st.write(f"**Sinyal & Internet Internal:** {row.get('Bagaimana kualitas sinyal telepon dan koneksi internet di dalam cabang?', '-')}")
                    st.write(f"**Kondisi Parkir:** {row.get('Kondisi parkir di depan cabang — mudah/sulit, berbayar/gratis?', '-')}")
                    st.write(f"**Isu Banjir / Akses Musiman:** {row.get('Apakah lokasi sering banjir atau ada kendala akses musiman?', '-')}")
                    st.write(f"**Luas Ruko Saat Ini:** {row.get('Berapa luas ruko atau cabang sekarang (meter persegi)?', '-')} m²")
                    st.write(f"**Kecukupan Luas Ruko:** {row.get('Apakah luas ruko atau cabang terasa cukup untuk operasional dan jumlah nasabah harian?', '-')}")
                    st.write(f"**Kendala Fisik / Rencana Renovasi:** {row.get('Apakah ada kendala fisik bangunan atau rencana renovasi yang ada?', '-')}")

                with st.expandable("⚔️ 4. Dinamika Kompetisi Lapangan"):
                    st.write(f"**Jumlah Kompetitor (Radius 500m):** {row.get('Berapa jumlah kompetitor dalam radius 500 m ?', '-')}")
                    st.write(f"**Nama-Nama Kompetitor:** {row.get('Jika ada kompetitor, sebutkan namanya', '-')}")
                    st.write(f"**Dampak Persaingan Terberat:** {row.get('Kompetitor yang paling dirasakan dampak persaingannya? (pegadaian swasta, koperasi simpan pinjam, bpr, rentenir, dll)', '-')}")
                    st.error(f"**🚨 Kompetitor Baru (3 Bulan Terakhir):** {row.get('Kompetitor baru yang muncul belakangan ini atau akhir-akhir ini (3 bulan terakhir). Nama & lokasi?', '-')}")
                    st.write(f"**Alasan Nasabah Pilih Kompetitor:** {row.get('Alasan utama nasabah memilih kompetitor dibanding kita (jika ada)', '-')}")
                    st.write(f"**Persepsi Biaya/Bunga vs Kompetitor:** {row.get('Persepsi nasabah terhadap biaya/bunga kita dibanding kompetitor:', '-')}")
                    st.write(f"**Penolakan Nasabah yang Sering Terjadi:** {row.get('Penolakan nasabah yang sering terjadi dan alasan utamanya?', '-')}")

                with st.expandable("📈 5. Karakteristik & Pola Musiman Nasabah"):
                    st.write(f"**Tipe Nasabah Dominan:** {row.get('Tipe nasabah yang paling dominan?', '-')}")
                    st.write(f"**Signifikansi Nasabah Loyal:** {row.get('Apakah ada nasabah loyal / repeat customer yang signifikan? Jika ada, sekitar berapa?', '-')}")
                    st.write(f"**Asal Radius Area Nasabah:** {row.get('Nasabah kebanyakan berasal dari radius / area mana saja?', '-')}")
                    st.write(f"**Nasabah Harian (Weekday):** {row.get('Rata-rata jumlah nasabah per hari WEEKDAY (Senin-Jumat)', '-')}")
                    st.write(f"**Nasabah Harian (Weekend):** {row.get('Rata-rata jumlah nasabah per hari WEEKEND (Sabtu-Minggu)', '-')}")
                    st.write(f"**Pola Musiman Sangat Jelas?:** {row.get('Apakah ada pola musiman omset yang sangat jelas?', '-')}")
                    st.write(f"**Detail Pola Musiman Karyawan:** {row.get('Ceritakan detail pola musiman yang dirasakan karyawan', '-')}")
                    st.write(f"**Estimasi Keluarga (Radius 500m):** {row.get('Perkiraan jumlah KK yang tinggal dalam radius 500 m cabang', '-')}")
                    st.write(f"**Mata Pencaharian Dominan:** {row.get('Mata pencaharian dominan warga sekitar cabang', '-')}")
            
            # =========================================================================
            # BAGIAN BAWAH: SARAN & REKOMENDASI STRATEGIS (LEBAR PENUH)
            # =========================================================================
            st.markdown("---")
            st.subheader("💡 Narasi Kualitatif & Strategi Optimalisasi Bisnis Cabang 2026")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                with st.container(border=True):
                    st.markdown("##### 🚀 Program Sukses & Potensi Wilayah")
                    st.write(f"**Program/Promosi Sukses Lampau:** {row.get('Program atau promosi yang pernah sangat berhasil & alasannya?', '-')}")
                    st.write(f"**Tingkat Ketergarapan Potensi Wilayah:** {row.get('Potensi wilayah sekitar cabang sudah tergarap maksimal atau masih belum?', '-')}")
                    st.write(f"**Fasilitas yang Paling Sering Diminta Nasabah:** {row.get('Keluhan atau fasilitas yang paling sering diminta nasabah (misal: dispenser, kursi tambahan)', '-')}")
                    st.write(f"**Produk Paling Potensial ke Depan:** {row.get('Menurut pengamatan anda, apa produk yang paling potensial untuk dikembangkan di wilayah cabang ini ke depan?', '-')}")
            
            with col_b2:
                with st.container(border=True):
                    st.markdown("##### 🚨 Saran, Kendala Kritis & Rekomendasi Utama")
                    st.warning(f"\"{row.get('Tuliskan saran, kendala kritis, atau rekomendasi strategis lainnya dari tim cabang untuk optimalisasi performa bisnis 2026', '-')}\"")

except Exception as e:
    st.error(f"Gagal memuat sistem dashboard. Pesan Error: {e}")
