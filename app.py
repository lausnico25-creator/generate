import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
import random
import re
from datetime import datetime

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="AI Video Studio", page_icon="🎥", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect('video_studio.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt TEXT, video_url TEXT, timestamp TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. API SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Batasan Sistem: Memaksa Gemini hanya fokus pada Video
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="Kamu adalah ahli sinematografi. Tugasmu HANYA mengubah prompt user menjadi deskripsi visual gerakan video (motion video) dalam bahasa Inggris. Jika user meminta sesuatu yang tidak berhubungan dengan video, tolak dengan sopan."
    )
except:
    st.error("API Key Gemini tidak ditemukan!")
    st.stop()

# --- 4. TAMPILAN UTAMA ---
st.title("🎥 Pro AI Video Generator")
st.write("Ubah teks menjadi visual video sinematik secara instan.")

# --- 5. INPUT & LOGIKA ---
with st.container(border=True):
    user_prompt = st.text_input("Deskripsikan video yang ingin dibuat:", placeholder="Contoh: Drone shot melintasi air terjun di hutan...")
    
    if st.button("🎬 Generate Video", use_container_width=True):
        if user_prompt:
            with st.spinner("Gemini sedang merancang pergerakan kamera..."):
                try:
                    # Perintah ke Gemini untuk membuat prompt video
                    response = model.generate_content(f"Buat prompt video sinematik untuk: {user_prompt}")
                    video_prompt_raw = response.text.strip()
                    
                    # Pembersihan karakter agar URL tidak pecah
                    clean_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', video_prompt_raw)
                    encoded_prompt = urllib.parse.quote(clean_prompt)
                    
                    # URL Generator (Menggunakan engine Pollinations dengan flag video)
                    seed = random.randint(1, 999999)
                    # Kita gunakan parameter &model=flux untuk kualitas terbaik yang mendukung motion look
                    final_video_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&seed={seed}&model=flux"
                    
                    # Simpan ke Database
                    c = conn.cursor()
                    c.execute("INSERT INTO history (prompt, video_url, timestamp) VALUES (?, ?, ?)", 
                              (user_prompt, final_video_url, datetime.now().strftime("%H:%M")))
                    conn.commit()
                    
                    st.success("Video Berhasil Dirancang!")
                    st.image(final_video_url, caption="Hasil Visual Video (Preview)", use_container_width=True)
                    st.info(f"💡 **AI Motion Prompt:** {video_prompt_raw}")
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
        else:
            st.warning("Masukkan prompt terlebih dahulu!")

# --- 6. RIWAYAT VIDEO ---
st.divider()
st.subheader("📁 Riwayat Video")
c = conn.cursor()
c.execute("SELECT prompt, video_url, timestamp FROM history ORDER BY id DESC")
rows = c.fetchall()

if rows:
    for p, url, t in rows:
        with st.expander(f"🕒 {t} - {p[:30]}..."):
            st.image(url, use_container_width=True)
            st.caption(f"Prompt asli: {p}")
else:
    st.write("Belum ada video yang dibuat.")
