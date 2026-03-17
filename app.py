import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
import random
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Gemini Visual Studio", page_icon="♊", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('gemini_visual.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, type TEXT, prompt TEXT, output_url TEXT, timestamp TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONEKSI API GEMINI ---
try:
    # Mengambil key dari Secrets Streamlit Cloud
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("⚠️ API Key Gemini belum terpasang di Secrets!")
    st.stop()

# --- 4. SIDEBAR (PROJECT HISTORY) ---
with st.sidebar:
    st.title("📁 Project Manager")
    if st.button("➕ Mulai Project Baru", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()

    st.divider()
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

# Logika untuk memastikan ada sesi yang aktif
if "current_sid" not in st.session_state or st.session_state.current_sid is None:
    if sessions: st.session_state.current_sid = sessions[0][0]
    else:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 5. TAMPILAN UTAMA ---
st.title("♊ Gemini Visual Studio")
st.write("Buat gambar dan visual secara gratis dengan bantuan AI Gemini.")

# Menampilkan hasil dari database
c = conn.cursor()
c.execute("SELECT type, prompt, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
history = c.fetchall()

for r_type, r_p, r_url in history:
    with st.container(border=True):
        st.write(f"**[{r_type.upper()}]** {r_p}")
        # Semua output ditampilkan sebagai image/visual yang relevan
        st.image(r_url, use_container_width=True)

# --- 6. INPUT AREA ---
st.write("---")
if user_prompt := st.chat_input("Contoh: Kapal pesiar di tengah badai petir"):
    st.session_state.active_p = user_prompt

if "active_p" in st.session_state and st.session_state.active_p:
    st.info(f"Target: **{st.session_state.active_p}**")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🖼️ Buat Gambar", use_container_width=True):
            with st.spinner("Gemini sedang memoles prompt..."):
                # Minta Gemini membuat prompt teknis Inggris yang bersih
                resp = model.generate_content(f"Create a detailed visual prompt for: {st.session_state.active_p}. English only, no quotes, no conversational text.")
                clean_prompt = urllib.parse.quote(resp.text.strip())
                
                # URL Generator dengan seed acak agar tidak pecah/stuck
                seed = random.randint(0, 99999)
                final_url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=1024&seed={seed}&model=flux"
                
                # Simpan & Update Judul
                c.execute("INSERT INTO results (session_id, type, prompt, output_url, timestamp) VALUES (?,?,?,?,?)",
                          (st.session_state.current_sid, "image", st.session_state.active_p, final_url, datetime.now().strftime("%H:%M")))
                c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (st.session_state.active_prompt[:15] if "active_prompt" in st.session_state else st.session_state.active_p[:15], st.session_state.current_sid))
                conn.commit()
                st.session_state.active_p = None
                st.rerun()

    with col2:
        if st.button("🎥 Buat Visual Video", use_container_width=True):
            with st.spinner("Sedang merancang visual..."):
                # Untuk Video, karena API Sora/Luma berbayar, kita buat visual sinematik yang relevan
                resp = model.generate_content(f"Create a cinematic, high-motion visual prompt for: {st.session_state.active_p}. English only, no quotes.")
                clean_prompt = urllib.parse.quote(resp.text.strip())
                
                seed = random.randint(0, 99999)
                # Menggunakan model 'flux' yang lebih sinematik
                final_url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=1024&seed={seed}&model=flux"
                
                c.execute("INSERT INTO results (session_id, type, prompt, output_url, timestamp) VALUES (?,?,?,?,?)",
                          (st.session_state.current_sid, "video", st.session_state.active_p, final_url, datetime.now().strftime("%H:%M")))
                conn.commit()
                st.session_state.active_p = None
                st.rerun()
