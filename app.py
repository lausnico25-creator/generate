import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_paste_button import paste_image_button
import io

# 1. INTEGRASI SECRETS
# Mengambil API Key dari menu Secrets Streamlit
try:
    # Nama variabel harus sama dengan yang Anda tulis di menu Secrets
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("API Key tidak ditemukan di Secrets. Pastikan Anda sudah mengaturnya di Streamlit Cloud.")
    st.stop()

# Konfigurasi Halaman Visora
st.set_page_config(page_title="Visora AI", layout="wide")

# UI Styling: Gelap, Minimalis, Animasi Hijau
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* Animasi Hijau */
    @keyframes border-glow {
        0% { border-color: #00ff41; }
        50% { border-color: #008f11; }
        100% { border-color: #00ff41; }
    }
    
    div[data-testid="stFileUploader"] {
        border: 1px solid #00ff41;
        border-radius: 10px;
        padding: 10px;
        animation: border-glow 3s infinite;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111;
        border-radius: 5px;
        color: #00ff41;
        font-weight: bold;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #008f11, #00ff41);
        color: black;
        border: none;
        border-radius: 8px;
        transition: 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

st.title("VISORA")

tab1, tab2 = st.tabs(["🔍 Deskripsi Detail", "🎨 Generate Nano Banana"])

# --- MENU 1: DESKRIPSI GAMBAR (GEMINI 1.5 PRO) ---
with tab1:
    col_u, col_o = st.columns(2)
    with col_u:
        img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], key="desc")
    
    if img_file:
        img = Image.open(img_file)
        st.image(img, width=400)
        
        if st.button("Jalankan Deskripsi"):
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt = (
                "Deskripsikan gambar ini secara detail. "
                "ATURAN KETAT: Dilarang menyebutkan/mendeskripsikan Etnis, Rambut, Gaya Rambut, "
                "warna Rambut, Kumis, Janggut, Jenggot, atau bagian kepala lainnya kecuali ekspresi wajah. "
                "Format: [Subjek] (gambar referensi) [aktivitas/pakaian/latar belakang]. "
                "DILARANG menggunakan kata pembuka."
            )
            
            try:
                response = model.generate_content([prompt, img])
                output_text = response.text.strip()
                
                st.subheader("Hasil Analisis:")
                st.write(output_text)
                # Tombol Salin otomatis dari st.code
                st.code(output_text, language=None)
            except Exception as e:
                st.error(f"Gagal: {e}")

# --- MENU 2: GENERATE GAMBAR (NANO BANANA 2 / GEMINI 3 FLASH) ---
with tab2:
    st.markdown("### Nano Banana 2 Engine")
    
    # Fitur Paste, Drag & Drop
    paste_btn = paste_image_button(label="📋 Klik & Paste Gambar dari Clipboard", key="pasted")
    upload_gen = st.file_uploader("Atau Seret Gambar ke Sini", type=["jpg", "png", "jpeg"])
    user_prompt = st.text_input("Input Prompt Modifikasi:")

    target_img = None
    if paste_btn.image:
        target_img = paste_btn.image
    elif upload_gen:
        target_img = Image.open(upload_gen)

    if target_img:
        st.image(target_img, caption="Referensi Terdeteksi", width=300)

    if st.button("🚀 Generate New Image"):
        # Nano Banana 2 bertenaga Gemini 3 Flash
        model = genai.GenerativeModel('gemini-3-flash') 
        
        with st.spinner("Nano Banana sedang memproses komposisi..."):
            try:
                response = model.generate_content([f"Base on this image, generate: {user_prompt}", target_img])
                
                # Output hasil
                st.markdown("---")
                st.image(target_img, caption="Output Result") # Placeholder output
                
                # Ikon Download & Preview
                c1, c2, c3 = st.columns([0.1, 0.1, 0.8])
                with c1: st.button("📥", help="Download")
                with c2: st.button("🔍", help="Preview")
                
            except Exception as e:
                st.error(f"Error Model: {e}")
