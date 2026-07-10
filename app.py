import re
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

# =============================================================================
# 1. KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="Dashboard Performa Terpadu 2026",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# 2. FUNGSI AMBIL DATA LIVE DARI GOOGLE SHEETS
# =============================================================================
@st.cache_data(ttl=600)
def load_data_from_link():
    sheet_id = "1Uh7sSoiGVQGB9QJWcsNvXIQsZJUXlOA5x_OVxpFCtrA"
    gid_summary = "1761779832"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_summary}"

    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()

    for col in ['Mismatch_RF', 'Mismatch_GWR', 'Mismatch_OLS']:
        if col in df.columns:
            df[col] = df[col].fillna('Match')

    return df


# =============================================================================
# 3. KAMUS & FUNGSI ANALISIS TEKS (Text Mining, Pareto, Sentimen)
# =============================================================================

# --- Kamus kategori kendala lapangan (untuk Pareto & Text Mining) -----------
KATEGORI_KENDALA = {
    "Kompetitor / Persaingan": [
        "kompetitor", "pesaing", "diskon", "predatory", "bakar uang", "promo gencar"
    ],
    "Akses & Parkir": [
        "akses", "jalan", "parkir", "macet", "banjir", "ditutup", "rusak", "proyek"
    ],
    "SDM & Operasional": [
        "karyawan", "staf", "sdm", "absen", "tidak masuk", "kurang orang", "pelayanan"
    ],
    "Sistem & Stok/Plafon": [
        "sistem", "error", "down", "stok", "kosong", "plafon", "taksiran", "limit"
    ],
    "Ekonomi & Daya Beli": [
        "sepi", "daya beli", "ekonomi", "turun", "menurun", "pemukiman sepi", "lesu"
    ],
    "Fisik Bangunan/Ruko": [
        "renovasi", "sempit", "luas ruko", "branding", "papan nama", "sinyal"
    ],
}

# --- Kamus sentimen lexicon-based Bahasa Indonesia (informal, konteks bisnis)
KATA_NEGATIF = [
    "kurang", "kosong", "rusak", "lambat", "sulit", "buruk", "turun", "sepi",
    "tutup", "macet", "kendala", "masalah", "komplain", "mengeluh", "menurun",
    "terbatas", "kekurangan", "tidak memadai", "tidak cukup", "susah",
    "bermasalah", "gagal", "hilang", "menghambat", "lemah", "minim", "sering tidak masuk",
    "predatory", "bakar uang", "banjir", "proyek", "ditutup", "ditolak",
]
KATA_POSITIF = [
    "baik", "lancar", "cukup", "berhasil", "meningkat", "ramai", "mudah",
    "strategis", "potensial", "bagus", "optimal", "memadai", "nyaman",
    "stabil", "berkembang", "lengkap", "aktif", "loyal", "signifikan", "sukses",
]


def kategorikan_teks(teks: str):
    """Kembalikan list kategori kendala yang match pada satu baris narasi."""
    if not isinstance(teks, str) or not teks.strip():
        return []
    teks_lower = teks.lower()
    hasil = []
    for kategori, keywords in KATEGORI_KENDALA.items():
        if any(kw in teks_lower for kw in keywords):
            hasil.append(kategori)
    return hasil


def hitung_sentimen(teks: str):
    """Skor sentimen sederhana: (pos - neg) / total_kata_match.
    Return (label, skor)."""
    if not isinstance(teks, str) or not teks.strip() or teks.strip() == "-":
        return "Tidak Ada Data", 0

    teks_lower = teks.lower()
    n_pos = sum(teks_lower.count(kw) for kw in KATA_POSITIF)
    n_neg = sum(teks_lower.count(kw) for kw in KATA_NEGATIF)

    if n_pos == 0 and n_neg == 0:
        return "Netral", 0

    skor = n_pos - n_neg
    if skor > 0:
        return "Positif", skor
    elif skor < 0:
        return "Negatif", skor
    return "Netral", 0


STOPWORDS_ID = set("""
yang di ke dari dan atau untuk dengan pada ini itu adalah ada tidak juga
saja bisa akan sudah belum masih karena jika kalau agar supaya nya nya,
tersebut para dalam oleh sebagai seperti lebih sangat cukup kami kita
mereka anda saya kepada tanpa antara namun tetapi hanya per bagi dsb dll
""".split())


def top_kata(seri_teks: pd.Series, n=40):
    """Hitung frekuensi kata (dibersihkan dari stopword) untuk word cloud/bar chart."""
    semua_teks = " ".join(seri_teks.dropna().astype(str).tolist()).lower()
    kata = re.findall(r"[a-zA-Zàáâã]{3,}", semua_teks)
    kata_bersih = [k for k in kata if k not in STOPWORDS_ID]
    return Counter(kata_bersih).most_common(n)


# =============================================================================
# 4. FUNGSI KLASIFIKASI KUADRAN PERFORMA
# =============================================================================
def klasifikasikan_kuadran(df, col_actual, col_pred):
    med_actual = df[col_actual].median()
    med_pred = df[col_pred].median()

    def _kuadran(row):
        aktual_tinggi = row[col_actual] >= med_actual
        pred_tinggi = row[col_pred] >= med_pred
        if not aktual_tinggi and pred_tinggi:
            return "Over-Predicted"
        elif aktual_tinggi and not pred_tinggi:
            return "Under-Predicted"
        elif aktual_tinggi and pred_tinggi:
            return "On-Track"
        else:
            return "Under-Performing"

    return df.apply(_kuadran, axis=1), med_actual, med_pred


# =============================================================================
# 5. LOAD DATA
# =============================================================================
try:
    df = load_data_from_link()

    col_actual = "Omzet_Actual"
    MODEL_MAP = {
        "Random Forest": ("Prediksi_Omzet_RF", "Mismatch_RF"),
        "OLS": ("Prediksi_Omzet_OLS", "Mismatch_OLS"),
        "GWR": ("Prediksi_Omzet_GWR", "Mismatch_GWR"),
    }

    st.title("Platform Audit & Performa Cabang")
    st.caption("Aplikasi Analisis Data Terpadu — Riset Lapangan & Prediksi Multi-Model 2026")

    # Pilihan model berlaku global untuk seluruh dashboard
    model_terpilih = st.selectbox(
        "🔧 Pilih Model Prediksi sebagai Basis Analisis:",
        list(MODEL_MAP.keys()),
        index=0
    )
    col_pred, col_mismatch = MODEL_MAP[model_terpilih]

    # Kolom bantu: kuadran performa (dihitung sekali, dipakai di semua tab)
    df["Kuadran_Performa"], med_actual, med_pred = klasifikasikan_kuadran(df, col_actual, col_pred)

    # Kolom bantu: sentimen per baris untuk 2 kolom naratif kunci
    COL_SDM = "Kendala utama terkait pengelolaan SDM di cabang saat ini"
    COL_SARAN = "Tuliskan saran, kendala kritis, atau rekomendasi strategis lainnya dari tim cabang untuk optimalisasi performa bisnis 2026"

    if COL_SDM in df.columns:
        sdm_hasil = df[COL_SDM].apply(hitung_sentimen)
        df["Sentimen_SDM_Label"] = sdm_hasil.apply(lambda x: x[0])
        df["Sentimen_SDM_Skor"] = sdm_hasil.apply(lambda x: x[1])
    if COL_SARAN in df.columns:
        saran_hasil = df[COL_SARAN].apply(hitung_sentimen)
        df["Sentimen_Saran_Label"] = saran_hasil.apply(lambda x: x[0])
        df["Sentimen_Saran_Skor"] = saran_hasil.apply(lambda x: x[1])

    # Kolom bantu: kategori kendala gabungan (untuk Pareto) dari beberapa kolom naratif
    KOLOM_NARATIF_KENDALA = [
        c for c in [
            COL_SDM,
            COL_SARAN,
            "Kendala utama yang memperlambat proses taksiran ?",
            "Jenis barang yang paling sering ditolak dan alasannya?",
        ] if c in df.columns
    ]

    def _gabung_kategori(row):
        gabungan_teks = " ".join(str(row[c]) for c in KOLOM_NARATIF_KENDALA if pd.notna(row[c]))
        return kategorikan_teks(gabungan_teks)

    if KOLOM_NARATIF_KENDALA:
        df["Kategori_Kendala"] = df.apply(_gabung_kategori, axis=1)

    # =========================================================================
    # NAVIGATION TABS
    # =========================================================================
    tab_exec, tab_deep, tab_naratif, tab_model = st.tabs([
        "Ringkasan Eksekutif",
        "Investigasi Deep-Dive Cabang",
        "Analisis Naratif & Sentimen",
        "Feature Validity & Rekomendasi Model",
    ])

    # =========================================================================
    # TAB 1: RINGKASAN EKSEKUTIF
    # =========================================================================
    with tab_exec:
        st.markdown(f"### Performa Global & Validasi Model — Basis: **{model_terpilih}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total Omset Aktual", value=f"Rp {df[col_actual].sum():,.0f}")
        with col2:
            st.metric(label=f"Total Prediksi Model ({model_terpilih})", value=f"Rp {df[col_pred].sum():,.0f}")
        with col3:
            total_mismatch = len(df[df[col_mismatch] == 'Mismatch'])
            st.metric(label=f"Cabang Mismatch ({model_terpilih}) 🚨", value=total_mismatch)
        with col4:
            if COL_SARAN in df.columns:
                terisi = df[COL_SARAN].notna() & (df[COL_SARAN].astype(str).str.strip() != "-")
                pct_isi = terisi.mean() * 100
                st.metric(label="Kelengkapan Form Riset ", value=f"{pct_isi:.0f}%")
            else:
                st.metric(label="Kelengkapan Form Riset ", value="N/A")

        st.markdown("---")

        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.subheader("Scatter Plot: Realisasi vs Prediksi (per Kuadran)")
            fig = px.scatter(
                df,
                x=col_pred,
                y=col_actual,
                color="Kuadran_Performa",
                hover_name="Nama Cabang",
                labels={col_pred: f"Prediksi Omzet ({model_terpilih})", col_actual: "Omzet Aktual"},
                color_discrete_map={
                    "Over-Predicted": "#EF553B",
                    "Under-Predicted": "#FFA15A",
                    "On-Track": "#636EFA",
                    "Under-Performing": "#AB63FA",
                }
            )
            fig.add_shape(
                type="line", x0=df[col_pred].min(), y0=df[col_pred].min(),
                x1=df[col_pred].max(), y1=df[col_pred].max(),
                line=dict(color="gray", dash="dash")
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Distribusi Kuadran")
            fig_pie = px.pie(df, names="Kuadran_Performa", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        st.subheader("Tabel Top 10 Gap Negatif Terbesar (Over-Predicted)")
        df_gap = df.copy()
        df_gap["Gap_Rp"] = df_gap[col_actual] - df_gap[col_pred]
        top10 = df_gap.sort_values("Gap_Rp").head(10)[
            ["Nama Cabang", "Kabupaten", col_actual, col_pred, "Gap_Rp", "Kuadran_Performa"]
        ]
        st.dataframe(top10, use_container_width=True)

        st.markdown("---")
        st.subheader("Database Terpadu Master (Live Stream)")
        st.dataframe(df, use_container_width=True)

    # =========================================================================
    # TAB 2: INVESTIGASI DEEP-DIVE CABANG
    # =========================================================================
    with tab_deep:
        st.markdown("### Lembar Kerja Audit Lapangan per Cabang")

        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            status_mismatch = st.selectbox("Saring Status:", ["Semua Cabang", f"Hanya Mismatch ({model_terpilih})"])
        with col_f2:
            filter_kuadran = st.selectbox(
                "Saring Kuadran:",
                ["Semua Kuadran", "Over-Predicted", "Under-Predicted", "On-Track", "Under-Performing"]
            )

        df_filtered = df.copy()
        if status_mismatch != "Semua Cabang":
            df_filtered = df_filtered[df_filtered[col_mismatch] == 'Mismatch']
        if filter_kuadran != "Semua Kuadran":
            df_filtered = df_filtered[df_filtered["Kuadran_Performa"] == filter_kuadran]

        list_cabang = df_filtered['Nama Cabang'].tolist()

        with col_f3:
            if not list_cabang:
                st.warning("Tidak ada cabang yang cocok dengan filter.")
                pilihan_cabang = None
            else:
                pilihan_cabang = st.selectbox("Pilih Target Cabang untuk Di-audit:", list_cabang)

        if pilihan_cabang:
            row = df[df['Nama Cabang'] == pilihan_cabang].iloc[0]

            st.markdown(f"####  Profil Target: **{row['Nama Cabang']}** ({row.get('Kabupaten', '-')})")

            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
            with col_m1:
                st.metric(label="Omzet Actual", value=f"Rp {row[col_actual]:,}")
            with col_m2:
                st.metric(label=f"Prediksi ({model_terpilih})", value=f"Rp {row[col_pred]:,}")
            with col_m3:
                st.metric(label="Premium Spot Score", value=f"{row.get('premium_spot_score', '-')}/100")
            with col_m4:
                st.metric(label="Kuadran", value=row.get("Kuadran_Performa", "-"))
            with col_m5:
                skor_sdm = row.get("Sentimen_SDM_Skor", 0)
                label_sdm = row.get("Sentimen_SDM_Label", "-")
                if label_sdm == "Negatif":
                    st.error(f"Sentimen SDM: {label_sdm}")
                elif label_sdm == "Positif":
                    st.success(f"Sentimen SDM: {label_sdm}")
                else:
                    st.info(f"Sentimen SDM: {label_sdm}")

            st.markdown("---")

            col_left, col_right = st.columns(2)

            # -----------------------------------------------------------
            # SISI KIRI: INDIKATOR MODEL & DATA DEMOGRAFI
            # -----------------------------------------------------------
            with col_left:
                st.info(" **Kondisi Fitur Model (Sisi Kuantitatif & Kewilayahan)**")

                with st.container(border=True):
                    st.markdown("#####  Demografi & Makro Wilayah")
                    st.write(f"- **Kabupaten:** {row.get('Kabupaten', '-')}")
                    st.write(f"- **Kategori Wilayah (Model):** {row.get('kategori_wilayah_mapped', row.get('kategori_wilayah', '-'))}")
                    st.write(f"- **Tipe Jalan (Model):** {row.get('jalan_mapped', row.get('tipe_jalan', '-'))}")
                    st.write(f"- **Total Penduduk:** {row.get('penduduk', 0):,} Jiwa")
                    st.write(f"- **Proporsi Usia Produktif:** {row.get('proporsi_usia_produktif', 0) * 100:.1f}%")
                    st.write(f"- **Tingkat Kemiskinan:** {row.get('kemiskinan', '-')}")
                    st.write(f"- **Rasio Pria/Wanita:** {row.get('proporsi_pria', '-')}/{row.get('proporsi_wanita', '-')}")
                    st.write(f"- **UMK Terpeta:** Rp {row.get('umk', 0):,}")

                with st.container(border=True):
                    st.markdown("#####  Indikator Spasial & Komersial")
                    st.write(f"- **Lebar Ruko:** {row.get('lebar_ruko', '-')} Meter")
                    st.write(f"- **Commercial Hub Index:** {row.get('commercial_hub_index', '-')}")
                    st.write(f"- **Fasilitas Belanja:** {row.get('jumlah_fasilitas_belanja', '-')}")
                    st.write(f"- **Jumlah Toko Ponsel:** {row.get('jumlah_toko_ponsel', '-')}")
                    st.write(f"- **Jumlah Pasar Tradisional:** {row.get('jumlah_pasar_tradisional', '-')}")
                    st.write(f"- **Jarak Ke Pasar Terdekat:** {row.get('jarak_pasar', '-')} Meter")
                    st.write(f"- **Jumlah Restoran:** {row.get('jumlah_restoran', '-')}")
                    st.write(f"- **Jumlah Kompetitor Spasial:** {row.get('jumlah_kompetitor', '-')}")
                    st.write(f"- **Kepadatan Kompetitor/Populasi:** {row.get('comp_per_pop', '-')}")

                with st.container(border=True):
                    st.markdown("#####  Evaluasi Multi-Model (Prediction Gap)")
                    st.write(f"- **Prediksi OLS:** Rp {row.get('Prediksi_Omzet_OLS', 0):,}")
                    st.write(f"- **Prediksi RF:** Rp {row.get('Prediksi_Omzet_RF', 0):,}")
                    st.write(f"- **Prediksi GWR:** Rp {row.get('Prediksi_Omzet_GWR', 0):,}")
                    st.write(f"- **Klaster Omzet:** {row.get('Klaster_Omzet', '-')}")
                    st.write(f"- **Cabang Terdekat Referensi:** {row.get('Cabang_Terdekat_Ref', '-')} ({row.get('Jarak_Ref_KM', '-')} KM)")

            # -----------------------------------------------------------
            # SISI KANAN: JAWABAN REAL LAPANGAN
            # -----------------------------------------------------------
            with col_right:
                st.warning(" **Realitas Riil Lapangan (Hasil Form Riset Lapangan)**")

                with st.expander(" 1. SDM & Operasional Cabang", expanded=True):
                    st.write(f"**Lama Beroperasi:** {row.get('Sudah beroperasi berapa lama cabang anda?', '-')}")
                    st.write(f"**Kategori Class Cabang:** {row.get('Kategori Class Cabang di lokasi anda', '-')}")
                    st.write(f"**Nama Kanit:** {row.get('Nama Kanit Cabang', '-')} ({row.get('Jabatan Karyawan', '-')})")
                    st.write(f"**Lama Bekerja di Cabang:** {row.get('Lama Bekerja di Cabang tersebut', '-')}")
                    st.write(f"**Jumlah Karyawan Aktif:** {row.get('Jumlah Karyawan Cabang Aktif Saat Ini', '-')}")
                    st.write(f"**Absensi (Sering Tidak Masuk?):** {row.get('Apakah sering ada karyawan yang tidak masuk?', '-')}")
                    st.write(f"**Keaktifan Jemput Bola/Promosi:** {row.get('Apakah karyawan aktif promosi /kunjungi / jemput bola nasabah?', '-')}")
                    st.error(f"**Kendala Utama SDM:** {row.get(COL_SDM, '-')}")
                    st.write(f"**Waktu Transaksi:** {row.get('Rata-rata waktu satu kali transaksi (menit) ?', '-')} Menit")
                    st.write(f"**Hambatan Taksiran:** {row.get('Kendala utama yang memperlambat proses taksiran ?', '-')}")

                with st.expander(" 2. Produk, Plafon & Kebijakan Taksiran"):
                    st.write(f"**Gadai Emas:** {row.get('Gadai Emas', '-')}")
                    st.write(f"**Gadai Elektronik:** {row.get('Gadai Elektronik', '-')}")
                    st.write(f"**Gadai BPKB:** {row.get('Gadai BPKB', '-')}")
                    st.write(f"**Gadai Lain-lain:** {row.get('Gadai lain-lain (sebutkan)', '-')}")
                    st.write(f"**Maksimum Plafon Saat Ini:** {row.get('Nilai taksiran maksimum yang bisa diproses cabang ini (plafon)?', '-')}")
                    st.write(f"**Butuh Kenaikan Plafon?:** {row.get('Apakah cabang membutuhkan kenaikan limit plafon taksiran?', '-')}")
                    st.write(f"**Alasan Penyesuaian Plafon:** {row.get('Jika butuh. Alasan utama kebutuhan penyesuaian plafon taksiran tersebut. Jika tidak butuh isi dengan \"Tidak\" atau \" - \"', '-')}")
                    st.error(f"**Barang Paling Sering Ditolak & Alasan:** {row.get('Jenis barang yang paling sering ditolak dan alasannya?', '-')}")

                with st.expander(" 3. Aksesibilitas, Fisik Ruko & Lingkungan"):
                    st.write(f"**Keterlihatan dari Jalan:** {row.get('Seberapa mudah kantor cabang terlihat dari jalan raya?', '-')}")
                    st.write(f"**Arah Hadap Bangunan:** {row.get('Arah hadap bangunan cabang', '-')}")
                    st.write(f"**Kondisi Papan Nama/Branding:** {row.get('Kondisi papan nama / branding cabang', '-')}")
                    st.write(f"**Sinyal & Internet Internal:** {row.get('Bagaimana kualitas sinyal telepon dan koneksi internet di dalam cabang?', '-')}")
                    st.write(f"**Kondisi Parkir:** {row.get('Kondisi parkir di depan cabang — mudah/sulit, berbayar/gratis?', '-')}")
                    st.write(f"**Isu Banjir / Akses Musiman:** {row.get('Apakah lokasi sering banjir atau ada kendala akses musiman?', '-')}")
                    st.write(f"**Luas Ruko Saat Ini:** {row.get('Berapa luas ruko atau cabang sekarang (meter persegi)?', '-')} m²")
                    st.write(f"**Kecukupan Luas Ruko:** {row.get('Apakah luas ruko atau cabang terasa cukup untuk operasional dan jumlah nasabah harian?', '-')}")
                    st.write(f"**Kendala Fisik / Rencana Renovasi:** {row.get('Apakah ada kendala fisik bangunan atau rencana renovasi yang ada?', '-')}")

                with st.expander(" 4. Dinamika Kompetisi Lapangan"):
                    st.write(f"**Jumlah Kompetitor (Radius 500m):** {row.get('Berapa jumlah kompetitor dalam radius 500 m ?', '-')}")
                    st.write(f"**Nama-Nama Kompetitor:** {row.get('Jika ada kompetitor, sebutkan namanya', '-')}")
                    st.write(f"**Dampak Persaingan Terberat:** {row.get('Kompetitor yang paling dirasakan dampak persaingannya? (pegadaian swasta, koperasi simpan pinjam, bpr, rentenir, dll)', '-')}")
                    st.error(f"** Kompetitor Baru (3 Bulan Terakhir):** {row.get('Kompetitor baru yang muncul belakangan ini atau akhir-akhir ini (3 bulan terakhir). Nama & lokasi?', '-')}")
                    st.write(f"**Alasan Nasabah Pilih Kompetitor:** {row.get('Alasan utama nasabah memilih kompetitor dibanding kita (jika ada)', '-')}")
                    st.write(f"**Persepsi Biaya/Bunga vs Kompetitor:** {row.get('Persepsi nasabah terhadap biaya/bunga kita dibanding kompetitor:', '-')}")
                    st.write(f"**Penolakan Nasabah yang Sering Terjadi:** {row.get('Penolakan nasabah yang sering terjadi dan alasan utamanya?', '-')}")

                with st.expander(" 5. Karakteristik & Pola Musiman Nasabah"):
                    st.write(f"**Tipe Nasabah Dominan:** {row.get('Tipe nasabah yang paling dominan?', '-')}")
                    st.write(f"**Signifikansi Nasabah Loyal:** {row.get('Apakah ada nasabah loyal / repeat customer yang signifikan? Jika ada, sekitar berapa?', '-')}")
                    st.write(f"**Asal Radius Area Nasabah:** {row.get('Nasabah kebanyakan berasal dari radius / area mana saja?', '-')}")
                    st.write(f"**Nasabah Harian (Weekday):** {row.get('Rata-rata jumlah nasabah per hari WEEKDAY (Senin-Jumat)', '-')}")
                    st.write(f"**Nasabah Harian (Weekend):** {row.get('Rata-rata jumlah nasabah per hari WEEKEND (Sabtu-Minggu)', '-')}")
                    st.write(f"**Pola Musiman Sangat Jelas?:** {row.get('Apakah ada pola musiman omset yang sangat jelas?', '-')}")
                    st.write(f"**Detail Pola Musiman Karyawan:** {row.get('Ceritakan detail pola musiman yang dirasakan karyawan', '-')}")
                    st.write(f"**Estimasi Keluarga (Radius 500m):** {row.get('Perkiraan jumlah KK yang tinggal dalam radius 500 m cabang', '-')}")
                    st.write(f"**Mata Pencaharian Dominan:** {row.get('Mata pencaharian dominan warga sekitar cabang', '-')}")

            st.markdown("---")
            st.subheader(" Narasi Kualitatif & Strategi Optimalisasi Bisnis Cabang 2026")

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                with st.container(border=True):
                    st.markdown("#####  Program Sukses & Potensi Wilayah")
                    st.write(f"**Program/Promosi Sukses Lampau:** {row.get('Program atau promosi yang pernah sangat berhasil & alasannya?', '-')}")
                    st.write(f"**Tingkat Ketergarapan Potensi Wilayah:** {row.get('Potensi wilayah sekitar cabang sudah tergarap maksimal atau masih belum?', '-')}")
                    st.write(f"**Fasilitas yang Paling Sering Diminta Nasabah:** {row.get('Keluhan atau fasilitas yang paling sering diminta nasabah (misal: dispenser, kursi tambahan)', '-')}")
                    st.write(f"**Produk Paling Potensial ke Depan:** {row.get('Menurut pengamatan anda, apa produk yang paling potensial untuk dikembangkan di wilayah cabang ini ke depan?', '-')}")

            with col_b2:
                with st.container(border=True):
                    st.markdown("#####  Saran, Kendala Kritis & Rekomendasi Utama")
                    label_saran = row.get("Sentimen_Saran_Label", "-")
                    st.caption(f"Sentimen Terdeteksi: **{label_saran}**")
                    st.warning(f"\"{row.get(COL_SARAN, '-')}\"")

    # =========================================================================
    # TAB 3: ANALISIS NARATIF & SENTIMEN
    # =========================================================================
    with tab_naratif:
        st.markdown("###  Text Mining, Pareto Kendala & Sentiment Analysis")

        col_filt1, col_filt2 = st.columns(2)
        with col_filt1:
            wilayah_opsi = ["Semua Wilayah"] + sorted(df["Kabupaten"].dropna().unique().tolist()) if "Kabupaten" in df.columns else ["Semua Wilayah"]
            filter_wilayah = st.selectbox("Filter Kabupaten/Wilayah:", wilayah_opsi)
        with col_filt2:
            filter_kuadran_naratif = st.selectbox(
                "Filter Kuadran Performa:",
                ["Semua Kuadran", "Over-Predicted", "Under-Predicted", "On-Track", "Under-Performing"],
                key="filter_kuadran_naratif"
            )

        df_naratif = df.copy()
        if filter_wilayah != "Semua Wilayah":
            df_naratif = df_naratif[df_naratif["Kabupaten"] == filter_wilayah]
        if filter_kuadran_naratif != "Semua Kuadran":
            df_naratif = df_naratif[df_naratif["Kuadran_Performa"] == filter_kuadran_naratif]

        st.markdown("---")
        st.subheader("A. Text Mining & Pareto Kategori Kendala")

        if "Kategori_Kendala" in df_naratif.columns:
            semua_kategori = [k for sublist in df_naratif["Kategori_Kendala"] for k in sublist]
            if semua_kategori:
                freq_kategori = Counter(semua_kategori)
                df_pareto = pd.DataFrame(freq_kategori.items(), columns=["Kategori", "Jumlah_Cabang"])
                df_pareto = df_pareto.sort_values("Jumlah_Cabang", ascending=False)
                df_pareto["Persentase"] = (df_pareto["Jumlah_Cabang"] / len(df_naratif) * 100).round(1)

                col_p1, col_p2 = st.columns([2, 1])
                with col_p1:
                    fig_pareto = px.bar(
                        df_pareto, x="Kategori", y="Jumlah_Cabang", text="Persentase",
                        title="Pareto Chart: Frekuensi Kategori Kendala Lapangan"
                    )
                    fig_pareto.update_traces(texttemplate="%{text}%", textposition="outside")
                    st.plotly_chart(fig_pareto, use_container_width=True)
                with col_p2:
                    st.dataframe(df_pareto, use_container_width=True, hide_index=True)

                st.markdown("#####  Drill-Down: Cabang per Kategori Kendala")
                kategori_pilih = st.selectbox("Pilih kategori untuk melihat detail narasi cabang:", df_pareto["Kategori"].tolist())
                mask_kategori = df_naratif["Kategori_Kendala"].apply(lambda lst: kategori_pilih in lst)
                kolom_tampil = ["Nama Cabang", "Kabupaten"] + KOLOM_NARATIF_KENDALA
                kolom_tampil = [c for c in kolom_tampil if c in df_naratif.columns]
                st.dataframe(df_naratif[mask_kategori][kolom_tampil], use_container_width=True)
            else:
                st.info("Belum ada kendala yang terdeteksi dari narasi pada filter saat ini.")

            st.markdown("#####  Kata Paling Sering Muncul di Narasi Lapangan")
            top_words = top_kata(
                pd.concat([df_naratif[c] for c in KOLOM_NARATIF_KENDALA if c in df_naratif.columns]),
                n=20
            )
            if top_words:
                try:
                    from wordcloud import WordCloud
                    import matplotlib.pyplot as plt

                    wc = WordCloud(width=900, height=350, background_color="white",
                                   colormap="Reds").generate_from_frequencies(dict(top_words))
                    fig_wc, ax = plt.subplots(figsize=(10, 4))
                    ax.imshow(wc, interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig_wc)
                except ImportError:
                    st.caption("Package `wordcloud` belum terinstal (`pip install wordcloud`) — menampilkan bar chart sebagai alternatif.")
                    df_words = pd.DataFrame(top_words, columns=["Kata", "Frekuensi"])
                    fig_words = px.bar(df_words, x="Kata", y="Frekuensi")
                    st.plotly_chart(fig_words, use_container_width=True)
            else:
                st.info("Tidak ada data teks yang cukup untuk analisis kata.")
        else:
            st.warning("Kolom narasi kendala tidak ditemukan pada dataset.")

        st.markdown("---")
        st.subheader("B. Sentiment Analysis (Lexicon-Based, Bahasa Indonesia)")
        st.caption(
            "Skor sentimen dihitung dari kemunculan kata kunci positif/negatif pada jawaban naratif. "
            "Metode ini adalah pendekatan cepat berbasis kamus kata; untuk akurasi kontekstual yang lebih tinggi, "
            "bisa di-upgrade ke model NLP (mis. BERT Multilingual) bila volume respons form sudah besar."
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if "Sentimen_SDM_Label" in df_naratif.columns:
                st.markdown("##### Distribusi Sentimen — Kendala SDM")
                fig_sdm = px.pie(df_naratif, names="Sentimen_SDM_Label", hole=0.4,
                                  color="Sentimen_SDM_Label",
                                  color_discrete_map={"Negatif": "#EF553B", "Positif": "#00CC96",
                                                       "Netral": "#636EFA", "Tidak Ada Data": "#B0B0B0"})
                st.plotly_chart(fig_sdm, use_container_width=True)
        with col_s2:
            if "Sentimen_Saran_Label" in df_naratif.columns:
                st.markdown("##### Distribusi Sentimen — Saran & Kendala Kritis")
                fig_saran = px.pie(df_naratif, names="Sentimen_Saran_Label", hole=0.4,
                                    color="Sentimen_Saran_Label",
                                    color_discrete_map={"Negatif": "#EF553B", "Positif": "#00CC96",
                                                         "Netral": "#636EFA", "Tidak Ada Data": "#B0B0B0"})
                st.plotly_chart(fig_saran, use_container_width=True)

        if "Sentimen_SDM_Skor" in df_naratif.columns:
            st.markdown("##### Rata-Rata Skor Sentimen SDM per Kuadran Performa")
            df_sent_kuadran = df_naratif.groupby("Kuadran_Performa")["Sentimen_SDM_Skor"].mean().reset_index()
            fig_sent_kuadran = px.bar(
                df_sent_kuadran, x="Kuadran_Performa", y="Sentimen_SDM_Skor",
                title="Semakin negatif skor, semakin buruk sentimen SDM cabang di kuadran tsb.",
                color="Sentimen_SDM_Skor", color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig_sent_kuadran, use_container_width=True)

        st.markdown("##### Tabel Cabang dengan Sentimen Paling Negatif")
        kolom_sent_tabel = ["Nama Cabang", "Kabupaten", "Kuadran_Performa"]
        if "Sentimen_SDM_Label" in df_naratif.columns:
            kolom_sent_tabel += ["Sentimen_SDM_Label", "Sentimen_SDM_Skor", COL_SDM]
        kolom_sent_tabel = [c for c in kolom_sent_tabel if c in df_naratif.columns]
        if "Sentimen_SDM_Skor" in df_naratif.columns:
            st.dataframe(
                df_naratif.sort_values("Sentimen_SDM_Skor")[kolom_sent_tabel].head(10),
                use_container_width=True
            )

    # =========================================================================
    # TAB 4: FEATURE VALIDITY & REKOMENDASI MODEL
    # =========================================================================
    with tab_model:
        st.markdown("###  Feature Validity Matrix & Rekomendasi Perbaikan Model")

        df_mismatch = df[df[col_mismatch] == 'Mismatch'].copy()

        st.subheader("A. Feature Validity Matrix (Cabang Mismatch)")
        st.caption(f"Dihitung dari {len(df_mismatch)} cabang berstatus Mismatch pada model {model_terpilih}.")

        if "Kategori_Kendala" in df_mismatch.columns and len(df_mismatch) > 0:
            semua_kategori_mismatch = [k for sublist in df_mismatch["Kategori_Kendala"] for k in sublist]
            freq_mismatch = Counter(semua_kategori_mismatch)
            df_validity = pd.DataFrame(freq_mismatch.items(), columns=["Kategori Kendala", "Jumlah Cabang Mismatch"])
            df_validity["% dari Total Mismatch"] = (
                df_validity["Jumlah Cabang Mismatch"] / max(len(df_mismatch), 1) * 100
            ).round(1)
            df_validity = df_validity.sort_values("% dari Total Mismatch", ascending=False)
            st.dataframe(df_validity, use_container_width=True, hide_index=True)

            if not df_validity.empty:
                top_faktor = df_validity.iloc[0]
                st.success(
                    f" **Insight :** {top_faktor['% dari Total Mismatch']:.0f}% cabang mismatch "
                    f"terindikasi terkait faktor **'{top_faktor['Kategori Kendala']}'**. "
                    f"Rekomendasi: pertimbangkan menambahkan fitur kuantitatif terkait faktor ini "
                    f"(misal skor/indikator numerik dari Form Riset) ke model prediksi berikutnya."
                )
        else:
            st.info("Tidak ada cabang mismatch atau kolom kategori kendala tidak tersedia.")

        st.markdown("---")
        st.subheader("B. Korelasi Faktor Kualitatif vs Besaran Gap")

        df_corr = df.copy()
        df_corr["Gap_Rp"] = df_corr[col_actual] - df_corr[col_pred]
        # Flag biner sederhana: apakah kategori kendala tsb terdeteksi pada cabang tsb
        if "Kategori_Kendala" in df_corr.columns:
            kategori_unik = list(KATEGORI_KENDALA.keys())
            for kat in kategori_unik:
                df_corr[f"Flag_{kat}"] = df_corr["Kategori_Kendala"].apply(lambda lst, k=kat: 1 if k in lst else 0)

            flag_cols = [f"Flag_{k}" for k in kategori_unik]
            korelasi = df_corr[flag_cols + ["Gap_Rp"]].corr()["Gap_Rp"].drop("Gap_Rp").sort_values()
            df_korelasi = korelasi.reset_index()
            df_korelasi.columns = ["Faktor Kendala", "Korelasi dengan Gap (Rp)"]
            df_korelasi["Faktor Kendala"] = df_korelasi["Faktor Kendala"].str.replace("Flag_", "")

            fig_corr = px.bar(
                df_korelasi, x="Faktor Kendala", y="Korelasi dengan Gap (Rp)",
                title="Korelasi negatif = faktor ini berasosiasi dengan gap semakin minus (over-prediksi)",
                color="Korelasi dengan Gap (Rp)", color_continuous_scale="RdBu"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            st.caption("Catatan: korelasi ini bersifat deskriptif (indikatif), bukan bukti kausalitas — perlu validasi lebih lanjut oleh tim Data Scientist.")
        else:
            st.info("Kolom kategori kendala tidak tersedia untuk analisis korelasi.")

        st.markdown("---")
        st.subheader("C. Peta Sebaran Cabang Mismatch & Kompetitor")

        if all(c in df.columns for c in ["latitude", "longitude"]):
            df_map = df.dropna(subset=["latitude", "longitude"]).copy()
            fig_map = px.scatter_mapbox(
                df_map, lat="latitude", lon="longitude",
                color="Kuadran_Performa", hover_name="Nama Cabang",
                hover_data={col_actual: True, col_pred: True, "latitude": False, "longitude": False},
                zoom=5, height=500,
                color_discrete_map={
                    "Over-Predicted": "#EF553B", "Under-Predicted": "#FFA15A",
                    "On-Track": "#636EFA", "Under-Performing": "#AB63FA",
                }
            )
            fig_map.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Kolom latitude/longitude tidak ditemukan untuk menampilkan peta.")

        st.markdown("---")
        st.subheader("D. Priority Action Matrix (Impact vs Actionability)")
        st.caption(
            "Sumbu X = besaran gap absolut (Rp, semakin ke kanan semakin material). "
            "Sumbu Y = actionability (Internal = 1, lebih mudah diperbaiki; Eksternal = 0, di luar kendali cabang)."
        )

        if "Kategori_Kendala" in df_mismatch.columns and len(df_mismatch) > 0:
            FAKTOR_INTERNAL = {"SDM & Operasional", "Sistem & Stok/Plafon", "Fisik Bangunan/Ruko"}
            FAKTOR_EKSTERNAL = {"Kompetitor / Persaingan", "Akses & Parkir", "Ekonomi & Daya Beli"}

            def _actionability(kategori_list):
                if not kategori_list:
                    return None
                n_internal = sum(1 for k in kategori_list if k in FAKTOR_INTERNAL)
                n_eksternal = sum(1 for k in kategori_list if k in FAKTOR_EKSTERNAL)
                total = n_internal + n_eksternal
                return round(n_internal / total, 2) if total > 0 else None

            df_priority = df_mismatch.copy()
            df_priority["Gap_Abs"] = (df_priority[col_actual] - df_priority[col_pred]).abs()
            df_priority["Actionability"] = df_priority["Kategori_Kendala"].apply(_actionability)
            df_priority = df_priority.dropna(subset=["Actionability"])

            if not df_priority.empty:
                fig_priority = px.scatter(
                    df_priority, x="Gap_Abs", y="Actionability",
                    hover_name="Nama Cabang", color="Kuadran_Performa",
                    labels={"Gap_Abs": "Besaran Gap (Rp, absolut)", "Actionability": "Skor Actionability (0=Eksternal, 1=Internal)"},
                    size="Gap_Abs"
                )
                st.plotly_chart(fig_priority, use_container_width=True)
                st.caption("Prioritas tertinggi: kanan-atas (gap besar & mudah diperbaiki/internal).")
            else:
                st.info("Belum cukup data kategori kendala pada cabang mismatch untuk membangun matrix ini.")
        else:
            st.info("Tidak ada cabang mismatch untuk dianalisis pada Priority Matrix.")

except Exception as e:
    st.error(f"Gagal memuat sistem dashboard. Pesan Error: {e}")
