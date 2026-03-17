import streamlit as st
import sqlite3
import google.generativeai as genai
import requests
import io
from PIL import Image
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Studio Gratis", page_icon="🎨", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('studio_free.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, type TEXT, prompt TEXT, output_data BLOB, timestamp TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONEKSI API ---
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"]
    
    genai.configure(api_key=GEMINI_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("Pastikan GEMINI_API_KEY dan HF_TOKEN sudah diisi di Secrets!")
    st.stop()

# --- 4. FUNGSI GENERATE GAMBAR (HUGGING FACE) ---
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_hf(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content

# --- 5. SIDEBAR (RIWAYAT) ---
with st.sidebar:
    st.title("📁 History")
    if st.button("➕ Project Baru", use_container_width=True):
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()

    st.write("---")
    c = conn.cursor()
    c.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    sessions = c.fetchall()
    for s_id, s_title in sessions:
        col_s, col_d = st.columns([4, 1])
        with col_s:
            if st.button(f"📄 {s_title}", key=f"s_{s_id}", use_container_width=True):
                st.session_state.current_sid = s_id
                st.rerun()
        with col_d:
            if st.button("🗑️", key=f"del_{s_id}"):
                c.execute("DELETE FROM sessions WHERE id = ?", (s_id,))
                c.execute("DELETE FROM results WHERE session_id = ?", (s_id,))
                conn.commit()
                st.session_state.current_sid = None
                st.rerun()

if "current_sid" not in st.session_state or st.session_state.current_sid is None:
    if sessions: st.session_state.current_sid = sessions[0][0]
    else:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 6. TAMPILAN UTAMA ---
st.title("🎓 AI Studio (Free Version)")

# Load riwayat dari database (dalam bentuk gambar binary)
c = conn.cursor()
c.execute("SELECT type, prompt, output_data FROM results WHERE session_id = ?", (st.session_state.current_sid,))
for r_type, r_p, r_data in c.fetchall():
    with st.container(border=True):
        st.write(f"**Prompt:** {r_p}")
        st.image(r_data, use_container_width=True)

# --- 7. INPUT AREA ---
st.write("---")
if prompt := st.chat_input("Deskripsikan gambar gratisanmu..."):
    st.session_state.temp_p = prompt

if "temp_p" in st.session_state and st.session_state.temp_p:
    st.info(f"Siap proses: **{st.session_state.temp_p}**")
    if st.button("🖼️ Generate Image (Free)", use_container_width=True):
        with st.spinner("Sedang memproses di server Hugging Face..."):
            # Optimasi prompt dengan Gemini agar hasilnya pro
            try:
                res_gemini = gemini_model.generate_content(f"Enhance this image prompt for Stable Diffusion, English only, short and powerful: {st.session_state.temp_p}")
                enhanced_prompt = res_gemini.text
            except:
                enhanced_prompt = st.session_state.temp_p
            
            # Panggil Hugging Face
            image_bytes = query_hf({"inputs": enhanced_prompt})
            
            # Simpan ke DB
            c.execute("INSERT INTO results (session_id, type, prompt, output_data, timestamp) VALUES (?,?,?,?,?)",
                      (st.session_state.current_sid, "image", st.session_state.temp_p, image_bytes, datetime.now().strftime("%H:%M")))
            c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (st.session_state.temp_p[:15], st.session_state.current_sid))
            conn.commit()
            
            st.session_state.temp_p = None
            st.rerun()
