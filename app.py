import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
import random
import re

# --- KONFIGURASI ---
st.set_page_config(page_title="AI Video Studio", page_icon="🎥")

# --- DATABASE ---
conn = sqlite3.connect('video_clean.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS vids (prompt TEXT, url TEXT)')
conn.commit()

# --- API SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Instruksi ketat agar Gemini hanya membuat prompt video
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction="Tugasmu hanya membuat 1 kalimat prompt video bahasa Inggris yang fokus pada gerakan (motion). Jangan gunakan simbol, tanda baca, atau kutip. Contoh: cinematic drone shot of mountains"
    )
except:
    st.error("API Key Gemini belum ada di Secrets!")
    st.stop()

# --- UI ---
st.title("🎥 AI Video Motion Studio")
st.write("Aplikasi ini khusus untuk membuat visual pergerakan video.")

prompt_input = st.text_input("Deskripsikan video (harus tentang video):")

if st.button("🎬 Buat Video", use_container_width=True):
    if prompt_input:
        with st.spinner("Sedang memproses visual video..."):
            # 1. Gemini merancang prompt
            res = model.generate_content(f"Video prompt untuk: {prompt_input}")
            raw_text = res.text.strip()
            
            # 2. SANITASI TOTAL (Kunci agar tidak broken page)
            # Menghapus semua karakter selain huruf dan angka
            clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', raw_text)
            # Menggabungkan dengan plus (+) bukan spasi agar URL valid
            encoded_prompt = clean_text.replace(" ", "+")
            
            # 3. GENERATE URL
            seed = random.randint(1, 100000)
            # Menggunakan aspek rasio video 16:9
            final_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&seed={seed}&model=flux&nologo=true"
            
            # 4. SIMPAN & TAMPILKAN
            c.execute("INSERT INTO vids VALUES (?, ?)", (prompt_input, final_url))
            conn.commit()
            
            st.image(final_url, caption="Preview Pergerakan Video", use_container_width=True)
            st.info(f"AI Prompt: {raw_text}")
    else:
        st.warning("Masukkan prompt terlebih dahulu.")

# --- RIWAYAT ---
st.divider()
st.subheader("📁 Koleksi Video")
c.execute("SELECT * FROM vids ORDER BY rowid DESC")
for p, u in c.fetchall():
    with st.expander(f"Video: {p[:30]}..."):
        st.image(u, use_container_width=True)
