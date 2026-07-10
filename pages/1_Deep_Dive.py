import streamlit as st
import pandas as pd

st.set_page_config(page_title="Deep-Dive Audit Cabang", layout="wide")
st.title("🔍 Deep-Dive Komparasi Fitur Model vs Realitas Lapangan")
st.markdown("---")

# Fungsi Re-use data dari link
@st.cache_data(ttl=3600)
def load_data_from_link():
    sheet_id = "1Uh7sSoiGVQGB9QJWcsNvXIQsZJUXlOA5x_OVxpFCtrA"
    gid_summary = "1761779832"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_summary}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    if 'Mismatch_RF' in df.columns:
        df['Mismatch_RF'] = df['Mismatch_RF'].fillna('Match')
    return df

try:
    df = load_data_from_link()
    
    # --- FILTER SIDEBAR ---
    st.sidebar.header("Navigasi Audit")
    status_mismatch = st.sidebar.selectbox("Filter Status Cabang:", ["Semua Cabang", "Hanya Mismatch RF"])

    if status_mismatch == "Hanya Mismatch RF":
        list_cabang = df[df['Mismatch_RF'] == 'Mismatch']['Nama Cabang'].tolist()
    else:
        list_cabang = df['Nama Cabang'].tolist()

    if not list_cabang:
        st.warning("Tidak ada cabang yang memenuhi kriteria filter.")
    else:
        pilihan_cabang = st.sidebar.selectbox("Pilih Cabang untuk Di-audit:", list_cabang)
        
        # Ambil 1 baris data spesifik cabang yang dipilih
        row = df[df['Nama Cabang'] == pilihan_cabang].iloc[0]

        # --- HEADER UTAMA ---
        st.markdown(f"## 🏢 Cabang: **{row['Nama Cabang']}** ({row['Kabupaten']})")
        
        col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
        with col_perf1:
            st.metric(label="Omzet Actual", value=f"Rp {row['Omzet_Actual']:,}")
        with col_perf2:
            st.metric(label="Prediksi Model RF", value=f"Rp {row['Prediksi_Omzet_RF']:,}")
        with col_perf3:
            st.metric(label="Premium Spot Score", value=f"{row['premium_spot_score']}/100")
        with col_perf4:
            if row['Mismatch_RF'] == 'Mismatch':
                st.error(f"Status: {row['Mismatch_RF']}")
            else:
                st.success(f"Status: {row['Mismatch_RF']}")

        st.markdown("---")

        # --- AUDIT DUA SISI ---
        col_left, col_right = st.columns(2)

        # 🤖 SISI KIRI: INDIKATOR DATA KUANTITATIF (MODEL)
        with col_left:
            st.info("🤖 **Kondisi Fitur Model (Sisi Kuantitatif)**")
            
            with st.container(border=True):
                st.markdown("#### 📊 Demografi & Wilayah")
                st.write(f"- **Kategori Wilayah (Mapped):** {row['kategori_wilayah_mapped']}")
                st.write(f"- **Tipe Jalan (Mapped):** {row['jalan_mapped']}")
                st.write(f"- **Total Penduduk Sekitar:** {row['penduduk']:,} Jiwa")
                st.write(f"- **Proporsi Usia Produktif:** {row['proporsi_usia_produktif'] * 100:.1f}%")
                st.write(f"- **Tingkat Kemiskinan:** {row['kemiskinan']}")
                st.write(f"- **UMK Wilayah:** Rp {row['umk']:,}")
                
            with st.container(border=True):
                st.markdown("#### 🛒 Hub Komersial & Infrastruktur Spasial")
                st.write(f"- **Lebar Ruko:** {row['lebar_ruko']} Meter")
                st.write(f"- **Commercial Hub Index:** {row['commercial_hub_index']}")
                st.write(f"- **Jumlah Kompetitor Spasial:** {row['jumlah_kompetitor']}")
                st.write(f"- **Fasilitas Belanja:** {row['jumlah_fasilitas_belanja']}")
                st.write(f"- **Jumlah Toko Ponsel:** {row['jumlah_toko_ponsel']}")
                st.write(f"- **Jarak ke Pasar Terdekat:** {row['jarak_pasar']} Meter")

        # 📋 SISI KANAN: REALITAS KUALITATIF SURVEI (LAPANGAN)
        with col_right:
            st.warning("📋 **Realitas Riil Lapangan (Hasil Form Riset Lapangan)**")
            
            with st.expandable("👥 1. Kendala SDM & Operasional Cabang", expanded=True):
                st.write(f"**Lama Beroperasi:** {row['Sudah beroperasi berapa lama cabang anda?']}")
                st.write(f"**Nama Kanit:** {row['Nama Kanit Cabang']} ({row['Jabatan Karyawan']})")
                st.write(f"**Jumlah Karyawan Aktif:** {row['Jumlah Karyawan Cabang Aktif Saat Ini']}")
                st.write(f"**Kendala Utama SDM:** {row['Kendala utama terkait pengelolaan SDM di cabang saat ini']}")
                st.write(f"**Waktu Transaksi:** {row['Rata-rata waktu satu kali transaksi (menit) ?']} Menit")
                st.write(f"**Kendala Hambatan Taksiran:** {row['Kendala utama yang memperlambat proses taksiran ?']}")

            with st.expandable("📍 2. Aksesibilitas Ruko & Kondisi Fisik"):
                st.write(f"**Keterlihatan Ruko dari Jalan:** {row['Seberapa mudah kantor cabang terlihat dari jalan raya?']}")
                st.write(f"**Arah Hadap Bangunan:** {row['Arah hadap bangunan cabang']}")
                st.write(f"**Kondisi Papan Nama/Branding:** {row['Kondisi papan nama / branding cabang']}")
                st.write(f"**Kondisi Parkir Depan Cabang:** {row['Kondisi parkir di depan cabang — mudah/sulit, berbayar/gratis?']}")
                st.write(f"**Isu Banjir / Akses Musiman:** {row['Apakah lokasi sering banjir atau ada kendala akses musiman?']}")

            with st.expandable("⚔️ 3. Dinamika Persaingan & Pasar Bebas"):
                st.write(f"**Jumlah Kompetitor Pengamatan Lapangan:** {row['Berapa jumlah kompetitor dalam radius 500 m ?']}")
                st.write(f"**Nama-Nama Kompetitor:** {row['Jika ada kompetitor, sebutkan namanya']}")
                st.write(f"**Dampak Persaingan Terberat:** {row['Kompetitor yang paling dirasakan dampak persaingannya? (pegadaian swasta, koperasi simpan pinjam, bpr, rentenir, dll)']}")
                st.error(f"**🚨 Kompetitor Baru (3 Bulan Terakhir):** {row['Kompetitor baru yang muncul belakangan ini atau akhir-akhir ini (3 bulan terakhir). Nama & lokasi?']}")
                st.write(f"**Alasan Nasabah Pilih Kompetitor:** {row['Alasan utama nasabah memilih kompetitor dibanding kita (jika ada)']}")

            with st.expandable("📈 4. Karakteristik Nasabah & Pola Musiman"):
                st.write(f"**Tipe Nasabah Dominan:** {row['Tipe nasabah yang paling dominan?']}")
                st.write(f"**Estimasi KK dalam Radius 500m:** {row['Perkiraan jumlah KK yang tinggal dalam radius 500 m cabang']}")
                st.write(f"**Detail Pola Musiman Omset:** {row['Ceritakan detail pola musiman yang dirasakan karyawan']}")

        # --- BAGIAN BAWAH: REKOMENDASI STRATEGIS ---
        st.markdown("---")
        st.subheader("💡 Saran, Kendala Kritis & Rekomendasi Strategis Tim Cabang 2026")
        st.success(f"\"{row['Tuliskan saran, kendala kritis, atau rekomendasi strategis lainnya dari tim cabang untuk optimalisasi performa bisnis 2026']}\"")

except Exception as e:
    st.error(f"Gagal memuat data pada halaman deep dive. Pesan Error: {e}")
