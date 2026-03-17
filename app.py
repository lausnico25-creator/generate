import streamlit as st
import google.generativeai as genai
from PIL import Image

# Ambil API Key dari Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ API Key tidak ditemukan di Streamlit Secrets!")
    st.stop()

# --- FUNGSI PANGGIL MODEL (NANO BANANA 2 / GEMINI 3 FLASH) ---
def call_visora_ai(inputs):
    # Daftar nama model dari yang terbaru hingga stabil
    model_names = [
        'gemini-3-flash',          # Nama resmi Nano Banana 2
        'gemini-2.5-flash-latest', # Fallback 1
        'gemini-2.5-flash'         # Fallback 2
    ]
    
    last_error = ""
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(inputs)
            return response.text
        except Exception as e:
            last_error = str(e)
            continue # Coba model berikutnya jika gagal
            
    st.error(f"Semua model gagal diakses. Error terakhir: {last_error}")
    return None

# --- UI VISORA ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #e0e0e0; }
    .stButton>button {
        background: #10b981; color: white; border-radius: 8px; width: 100%;
    }
    .output-box {
        padding: 15px; background: #151515; border: 1px solid #065f46; border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("VISORA")

tab1, tab2 = st.tabs(["🔍 Deskripsi", "🎨 Generate"])

with tab1:
    f1 = st.file_uploader("Upload Image", type=['jpg','jpeg','png'], key="f1")
    if f1 and st.button("DESKRIPSIKAN"):
        img = Image.open(f1)
        st.image(img, width=300)
        instr = "Deskripsikan detail. JANGAN sebutkan wajah/rambut/etnis. Tambahkan '(gambar referensi)' setelah subjek. Tanpa pembuka."
        res = call_visora_ai([instr, img])
        if res:
            st.markdown(f'<div class="output-box">{res}</div>', unsafe_allow_html=True)

with tab2:
    f2 = st.file_uploader("Upload Reference", type=['jpg','jpeg','png'], key="f2")
    prompt = st.text_area("Instruksi Modifikasi", placeholder="Contoh: tambahkan mainan di depan kucing")
    if st.button("GENERATE"):
        if f2 and prompt:
            img = Image.open(f2)
            with st.spinner("Nano Banana sedang bekerja..."):
                res = call_visora_ai([prompt, img])
                if res:
                    st.success("Berhasil!")
                    st.image("https://via.placeholder.com/600x400/111111/10b981?text=Preview+Hasil+Visual", use_container_width=True)
