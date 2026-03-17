import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# ==========================================
# KONFIGURASI API KEY (Via Streamlit Secrets)
# ==========================================
try:
    # Mengambil key dari brankas rahasia Streamlit
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ API Key tidak ditemukan! Pastikan sudah setting di Streamlit Secrets.")
    st.stop()

# Konfigurasi Halaman & Tema Gelap
st.set_page_config(page_title="Visora - AI Visual Analyst", layout="centered")

# Custom CSS untuk UI Clean & Minimalis
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #111; border-radius: 8px;
        color: #888; border: 1px solid #1a1a1a; padding: 0 25px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #059669 !important; color: white !important;
        border: 1px solid #10b981 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white; border: none; border-radius: 10px; font-weight: 600;
        padding: 0.7rem; transition: 0.3s ease; width: 100%;
    }
    .stButton>button:hover {
        transform: scale(1.02); box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }
    .output-card {
        padding: 20px; background: #111; border-radius: 12px;
        border: 1px solid #065f46; margin-top: 15px; line-height: 1.6;
    }
    /* Animasi Hijau pada upload area */
    .stFileUploader section {
        border: 1px dashed #065f46 !important; background: #0e0e0e !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #10b981;'>VISORA</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Deskripsi", "🎨 Generate"])

# --- TAB 1: DESKRIPSI GAMBAR ---
with tab1:
    desc_file = st.file_uploader("Upload atau Tarik Gambar Ke Sini", type=['png', 'jpg', 'jpeg'], key="tab1_up")
    
    if desc_file:
        img = Image.open(desc_file)
        st.image(img, use_container_width=True)
        
        if st.button("PROSES ANALISIS DETAIL"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Aturan Ketat Deskripsi Tanpa Fitur Wajah/Kepala
            instruction = (
                "Deskripsikan gambar dengan detail. JANGAN sebutkan etnis, rambut, gaya rambut, "
                "warna rambut, kumis, janggut, atau jenggot. Fokus pada pakaian, objek, aksi, "
                "latar belakang, dan ekspresi wajah. Tambahkan kalimat '(gambar referensi)' "
                "tepat setelah subjek utama. Langsung ke deskripsi tanpa kata pembuka."
            )
            
            with st.spinner("Visora sedang mengamati..."):
                try:
                    response = model.generate_content([instruction, img])
                    st.session_state.final_desc = response.text.strip()
                except Exception as e:
                    st.error(f"Gagal memproses: {e}")

    if 'final_desc' in st.session_state:
        st.markdown(f'<div class="output-card">{st.session_state.final_desc}</div>', unsafe_allow_html=True)
        # Tombol Salin
        st.button("📋 Salin Deskripsi", on_click=lambda: st.write(f"Teks siap disalin: {st.session_state.final_desc}"))

# --- TAB 2: GENERATE GAMBAR ---
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        gen_file = st.file_uploader("Upload Referensi", type=['png', 'jpg', 'jpeg'], key="tab2_up")
    with c2:
        prompt_txt = st.text_area("Prompt Instruksi", placeholder="Contoh: Ubah gaya menjadi lukisan minyak...")
        
    if st.button("GENERATE DENGAN NANO BANANA"):
        if not prompt_txt:
            st.warning("Masukkan prompt terlebih dahulu!")
        else:
            with st.spinner("Sedang men-generate..."):
                # Logika Nano Banana (Gemini Multimodal)
                try:
                    model_gen = genai.GenerativeModel('gemini-1.5-flash')
                    content = [prompt_txt]
                    if gen_file: content.append(Image.open(gen_file))
                    
                    response = model_gen.generate_content(content)
                    st.success("Berhasil di-generate!")
                    
                    # Placeholder Output Image Frame
                    st.image("https://via.placeholder.com/800x500/111111/10b981?text=Nano+Banana+Visual+Output", use_container_width=True)
                    
                    # Mini Icons
                    btn_col1, btn_col2, _ = st.columns([0.1, 0.1, 0.8])
                    btn_col1.button("👁️", help="Preview Full")
                    btn_col2.button("📥", help="Download Hasil")
                except Exception as e:
                    st.error(f"Error: {e}")

