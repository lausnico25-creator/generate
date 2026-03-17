import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_paste_button import paste_image_button
import io

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="Visora AI", layout="centered")

# Custom CSS untuk Tema Gelap, Animasi Hijau, dan UI Minimalis
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Global Green Animation for Borders */
    @keyframes glow {
        0% { border-color: #1ed760; box-shadow: 0 0 5px #1ed760; }
        50% { border-color: #39ff14; box-shadow: 0 0 20px #39ff14; }
        100% { border-color: #1ed760; box-shadow: 0 0 5px #1ed760; }
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border: 1px solid #1ed760 !important;
        background-color: #161b22 !important;
        color: white !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        background-color: #161b22;
        border-radius: 5px;
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid #1ed760 !important;
    }

    /* Clean UI for Buttons */
    .stButton>button {
        width: 100%;
        background-color: #1ed760;
        color: black;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #39ff14;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar untuk API Key
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

st.title("VISORA")

tab1, tab2 = st.tabs(["🔍 Deskripsi Gambar", "🎨 Generate Gambar"])

# --- TAB 1: DESKRIPSI GAMBAR ---
with tab1:
    uploaded_file = st.file_uploader("Upload gambar untuk dideskripsikan", type=["jpg", "jpeg", "png"], key="desc_upload")
    
    if uploaded_file and api_key:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        
        if st.button("Deskripsikan Gambar"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Prompt dengan aturan ketat
            prompt = (
                "Deskripsikan gambar ini dengan detail. "
                "ATURAN KETAT: Dilarang menyebutkan etnis, rambut, gaya rambut, warna rambut, kumis, janggut, jenggot, "
                "atau detail fisik wajah dan kepala lainnya kecuali ekspresi wajah. "
                "Gunakan format: [Subjek] (gambar referensi) sedang [aktivitas/detail lainnya]. "
                "Jangan gunakan kata pembuka seperti 'Gambar ini menunjukkan' atau 'Di dalam foto ini'."
            )
            
            try:
                response = model.generate_content([prompt, img])
                result_text = response.text.strip()
                
                st.subheader("Output:")
                st.write(result_text)
                st.code(result_text, language=None) # Tombol salin bawaan Streamlit
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: GENERATE GAMBAR ---
with tab2:
    st.write("Upload, Drag-and-Drop, atau Paste gambar untuk referensi:")
    
    # Fitur Paste dari Clipboard
    pasted_img = paste_image_button(label="📋 Paste Image from Clipboard", key="paste_btn")
    uploaded_gen_file = st.file_uploader("Atau pilih file...", type=["jpg", "jpeg", "png"], key="gen_upload")
    
    user_prompt = st.text_area("Input Prompt (instruksi perubahan/penambahan)")
    
    final_img = None
    if pasted_img:
        final_img = pasted_img.image
    elif uploaded_gen_file:
        final_img = Image.open(uploaded_gen_file)
        
    if final_img:
        st.image(final_img, caption="Gambar Referensi", width=300)
    
    if st.button("Generate Gambar"):
        if api_key and final_img and user_prompt:
            with st.spinner("Nano Banana sedang memproses..."):
                # Catatan: Logika ini menggunakan Gemini (multimodal) untuk mensimulasikan output 'Nano Banana'
                # sesuai batasan API yang tersedia untuk developer saat ini.
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                try:
                    # Simulasi response (Gemini saat ini mengembalikan teks, 
                    # namun di sini kita menyiapkan UI untuk output gambar di masa depan/API khusus)
                    st.info("Fitur Image Generation via API memerlukan akses model Imagen/Nano Banana. Menampilkan preview simulasi...")
                    
                    # Placeholder untuk hasil gambar
                    st.image(final_img, caption="Hasil Generasi (Preview)", use_container_width=True)
                    
                    # Ikon Kecil untuk Download dan Preview
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.download_button("💾 Download", data=uploaded_gen_file if uploaded_gen_file else b"data", file_name="visora_gen.png")
                    with col2:
                        st.button("🔍 Preview Fullscreen")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Pastikan API Key, Gambar, dan Prompt sudah terisi.")
