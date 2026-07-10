import streamlit as st
import pandas as pd

st.set_page_config(page_title="Deep-Dive Analisis", layout="wide")
st.title("Deep-Dive Geografis & Audit Laporan Form Riset")

# Dummy Load dari gabungan baris CSV Anda
# Di dunia nyata, Anda tinggal mengambil baris cabang tertentu berdasarkan filter
@st.cache_data
def load_full_features():
    return pd.DataFrame({
        'nama_cabang': ['MDN001', 'KNG014', 'PTI001'],
        'umk': [4500000, 3200000, 2800000],
        'lebar_ruko': [8, 6, 7],
        'jumlah_kompetitor': [1, 3, 2],
        'premium_spot_score': [85, 45, 70],
        'Jarak_Ref_KM': [0.5, 3.2, 1.8],
        'Cabang_Terdekat_Ref': ['MDN004', 'KNG002', 'PTI003']
    })

df_feat = load_full_features()

# --- SIDEBAR FILTER ---
st.sidebar.header("Navigasi Cabang")
pilihan_cabang = st.sidebar.selectbox("Pilih Cabang untuk Di-audit:", df_feat['nama_cabang'].tolist())

# Ambil data spesifik cabang yang dipilih
cabang_data = df_feat[df_feat['nama_cabang'] == pilihan_cabang].iloc[0]

st.markdown(f"### Audit Indikator & Feedback Lapangan: **{pilihan_cabang}**")

# --- KOMPARASI DUA SISI ---
col_features, col_form = st.columns(2)

with col_features:
    st.info("🤖 **Kondisi Fitur Model (Data Kuantitatif di CSV)**")
    
    # Kelompokkan visualisasi berdasarkan variabel Anda
    st.markdown("####  Aspek Makro & Properti")
    st.write(f"- **Nilai UMK daerah:** Rp {cabang_data['umk']:,}")
    st.write(f"- **Lebar Ruko:** {cabang_data['lebar_ruko']} Meter")
    st.write(f"- **Premium Spot Score:** {cabang_data['premium_spot_score']}/100")
    
    st.markdown("####  Aspek Spasial & Kompetisi")
    st.write(f"- **Jumlah Kompetitor Terdekat:** {cabang_data['jumlah_kompetitor']}")
    st.write(f"- **Cabang Referensi Terdekat:** {cabang_data['Cabang_Terdekat_Ref']}")
    st.write(f"- **Jarak ke Cabang Referensi:** {cabang_data['Jarak_Ref_KM']} KM")

with col_form:
    st.warning(" **Input Konteks Kualitatif (Data Hasil Google Form)**")
    
    # Bagian ini membaca text input / form kualitatif yang diisi manual oleh tim cabang Anda
    st.markdown("####  Alasan Kesenjangan / Kendala Lapangan")
    
    # Contoh logic penayangan dinamis berdasarkan nama_cabang
    if pilihan_cabang == 'MDN001':
        st.error("**Kendala Aksesibilitas:** 'Meskipun Premium Spot Score tinggi, jalanan di depan ruko sedang dibongkar untuk perbaikan drainase kota total sejak awal bulan. Parkir mobil/motor lumpuh.'")
        st.markdown("**Catatan Kompetisi:** '1 Kompetitor melakukan promo potong admin besar-besaran untuk mengalihkan rute konsumen.'")
    elif pilihan_cabang == 'PTI001':
        st.error("**Kendala Operasional:** 'Stok inventaris terlambat datang dari gudang pusat regional, banyak konsumen yang membatalkan transaksi karena barang kosong.'")
    else:
        st.success("Belum ada kendala kritikal yang dilaporkan atau cabang berstatus Match.")

st.markdown("---")
# Menampilkan peta sederhana jika longitude & latitude dimasukkan
st.subheader("Lokasi Cabang Terkait")
st.caption("Gunakan data latitude dan longitude dari CSV Anda untuk memetakan sebaran titik rawan mismatch.")
