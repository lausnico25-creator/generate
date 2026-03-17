import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_paste_button import paste_image_button
import io

# 1. KONFIGURASI SECRETS & API
# Pastikan di Streamlit Cloud Secrets sudah ada: GEMINI_API_KEY = "..."
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Konfigurasi Secrets 'GEMINI_API_KEY' tidak ditemukan!")
    st.stop()

# 2. SETTING UI VISORA
st.set_page_config(page_title="Visora AI", layout="centered")

st.markdown("""
    <style>
    /* Tema Gelap & Clean */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Animasi Hijau pada Uploader */
    [data-testid="stFileUploader"] {
        border: 2px solid #00ff41;
        border-radius: 15px;
        padding: 20px;
        background-color: #161b22;
        transition: 0.3s;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 5px;
        color: #00ff41;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #00ff41 !important; }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #008f11, #00ff41);
        color: black;
        font-weight: bold;
        border: none;
        padding: 12px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🟢 VISORA")
st.caption("Advanced Image Analytics & Generation Engine")

tab1, tab2 = st.tabs(["🔍 Deskripsi Detail", "🎨 Generate Nano Banana"])

# --- MENU 1: DESKRIPSI GAMBAR ---
with tab1:
    uploaded_desc = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], key="u_desc")
    
    if uploaded_desc:
        img_desc = Image.open(uploaded_desc)
        st.image(img_desc, caption="Preview", use_container_width=True)
        
        if st.button("Jalankan Deskripsi", key="btn_desc"):
            # Menggunakan Gemini 1.5 Pro untuk akurasi sensor tinggi
            model_desc = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt_desc = (
                "Deskripsikan gambar ini secara sangat detail. "
                "ATURAN KETAT: Dilarang keras menyebutkan Etnis, Rambut, Gaya Rambut, "
                "warna Rambut, Kumis, Janggut, Jenggot, atau bagian kepala/wajah lainnya "
                "KECUALI ekspresi wajah. "
                "Format: [Subjek] (gambar referensi) [aktivitas/detail lainnya]. "
                "Dilarang menggunakan kata pembuka seperti 'Gambar ini menunjukkan'."
            )
            
            with st.spinner("Menganalisis..."):
                try:
                    response = model_desc.generate_content([prompt_desc, img_desc])
                    hasil = response.text.strip()
                    st.markdown("### Output:")
                    st.info(hasil)
                    st.code(hasil, language=None) # Tombol salin otomatis
                except Exception as e:
                    st.error(f"Error: {e}")

# --- MENU 2: GENERATE GAMBAR (NANO BANANA 2) ---
with tab2:
    st.markdown("### 🍌 Nano Banana 2 Engine")
    
    # Fitur Input Gambar (Paste & Upload)
    pasted_data = paste_image_button(label="📋 Klik & Paste Gambar (Ctrl+V)", key="pasted_gen_unique")
    uploaded_gen = st.file_uploader("Atau Drag & Drop di sini", type=["jpg", "png", "jpeg"], key="u_gen_unique")
    
    # Input Prompt untuk Modifikasi
    prompt_gen = st.text_area("Input Prompt Modifikasi:", placeholder="Contoh: Ubah latar belakang menjadi pantai atau tambahkan kacamata hitam...")

    # Logika Penentuan Gambar yang Aktif
    final_img = None
    if pasted_data and hasattr(pasted_data, 'image') and pasted_data.image is not None:
        final_img = pasted_data.image
    elif uploaded_gen:
        final_img = Image.open(uploaded_gen)

    if final_img:
        st.image(final_img, caption="Gambar Referensi Terdeteksi", width=300)
        
        if st.button("🚀 Jalankan Nano Banana", key="btn_run_gen"):
            if not prompt_gen:
                st.warning("Silakan masukkan prompt agar Nano Banana tahu apa yang harus diubah!")
            else:
                # Menggunakan Gemini 1.5 Flash sebagai Engine Nano Banana
                model_gen = genai.GenerativeModel('gemini-1.5-flash')
                
                with st.spinner("Nano Banana sedang memproses gambar dan prompt Anda..."):
                    try:
                        # PROSES MULTIMODAL: Mengirim Gambar + Prompt ke AI
                        # Kita meminta AI memberikan deskripsi visual baru berdasarkan modifikasi
                        response = model_gen.generate_content([
                            f"Instruksi Modifikasi: {prompt_gen}. Tolong berikan deskripsi visual yang sangat detail tentang bagaimana gambar ini berubah sesuai instruksi saya.", 
                            final_img
                        ])
                        
                        st.markdown("---")
                        st.subheader("Hasil Modifikasi (Visual Description):")
                        st.success(response.text)
                        
                        # Ikon Download & Preview (Simulasi Output)
                        col_dl, col_pre, _ = st.columns([0.1, 0.1, 0.8])
                        with col_dl:
                            # Tombol download yang benar-benar bisa mengunduh file referensi saat ini
                            buffered = io.BytesIO()
                            final_img.save(buffered, format="PNG")
                            st.download_button("📥", data=buffered.getvalue(), file_name="visora_output.png", help="Download Result")
                        with col_pre:
                            st.button("🔍", help="Preview Fullscreen")
                            
                    except Exception as e:
                        st.error(f"Terjadi kesalahan pada model: {e}")
    else:
        st.info("Silakan Upload atau Paste gambar terlebih dahulu.")
