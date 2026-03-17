import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Pastikan Secrets sudah terisi di Streamlit Dashboard
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ API Key tidak ditemukan di Secrets!")
    st.stop()

# --- Fungsi Global untuk Memanggil AI ---
def call_visora_ai(content_list):
    # Menggunakan 'gemini-3-flash-latest' agar tidak error 404
    model = genai.GenerativeModel('gemini-3.0-flash-latest')
    response = model.generate_content(content_list)
    return response.text

# --- UI VISORA ---
st.set_page_config(page_title="Visora", layout="centered")

# (Gunakan CSS yang sama seperti sebelumnya untuk tema gelap)
st.markdown("<h1 style='text-align: center; color: #10b981;'>VISORA</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Deskripsi", "🎨 Generate"])

with tab1:
    desc_file = st.file_uploader("Upload Gambar", type=['png', 'jpg', 'jpeg'], key="up1")
    if desc_file:
        img = Image.open(desc_file)
        st.image(img, use_container_width=True)
        if st.button("PROSES ANALISIS"):
            with st.spinner("Menganalisis..."):
                instr = "Deskripsikan detail. JANGAN sebutkan etnis/rambut/wajah. Tambahkan '(gambar referensi)' setelah subjek. Tanpa pembuka."
                res = call_visora_ai([instr, img])
                st.info(res)

with tab2:
    gen_file = st.file_uploader("Upload Referensi", type=['png', 'jpg', 'jpeg'], key="up2")
    prompt_txt = st.text_area("Prompt Instruksi", placeholder="Contoh: buat agar ada mainan di depan kucing")
    
    if st.button("GENERATE DENGAN NANO BANANA"):
        if not prompt_txt:
            st.warning("Isi prompt dulu!")
        else:
            with st.spinner("Memproses visual..."):
                try:
                    # Gabungkan gambar (jika ada) dan prompt teks
                    inputs = [prompt_txt]
                    if gen_file:
                        inputs.append(Image.open(gen_file))
                    
                    res = call_visora_ai(inputs)
                    st.success("Analisis Perubahan Berhasil!")
                    # Frame Output
                    st.image("https://via.placeholder.com/800x500/111111/10b981?text=Visual+Result+Preview", use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")
