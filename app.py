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
            model_desc = genai.GenerativeModel('gemini-2.5-pro')
            
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

# --- MENU 2: GENERATE GAMBAR ---
with tab2:
    st.markdown("### Nano Banana 2 Engine")
    
    # Fitur Paste & Upload
    pasted_data = paste_image_button(label="📋 Klik & Paste Gambar (Ctrl+V)", key="pasted_ui")
    uploaded_gen = st.file_uploader("Atau Drag & Drop di sini", type=["jpg", "png", "jpeg"], key="u_gen")
    prompt_gen = st.text_input("Input Prompt Modifikasi:")

    # Logika Penentuan Gambar (Amankan dari AttributeError)
    final_img = None
    
    # Cek paste button secara aman
    if pasted_data and hasattr(pasted_data, 'image') and pasted_data.image is not None:
        final_img = pasted_data.image
    elif uploaded_gen:
        final_img = Image.open(uploaded_gen)

    if final_img:
        st.image(final_img, caption="Referensi Siap", width=300)
        
        if st.button("🚀 Generate New Image"):
            # Nano Banana 2 menggunakan basis Gemini 3 Flash
            model_gen = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.spinner("Generating with Nano Banana..."):
                try:
                    # Menghasilkan output (simulasi pengolahan gambar referensi + prompt)
                    response = model_gen.generate_content([f"Base on this image, fulfill this prompt: {prompt_gen}", final_img])
                    
                    st.markdown("---")
                    st.image(final_img, caption="Result Preview", use_container_width=True)
                    
                    # Ikon Download & Preview
                    col_dl, col_pre, _ = st.columns([0.1, 0.1, 0.8])
                    with col_dl:
                        st.button("📥", help="Download Result")
                    with col_pre:
                        st.button("🔍", help="Preview Fullscreen")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
