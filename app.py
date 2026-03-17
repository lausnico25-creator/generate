import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
import random
import re
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Gemini Visual Studio", page_icon="♊", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('gemini_visual_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, type TEXT, prompt TEXT, output_url TEXT, timestamp TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONEKSI API GEMINI ---
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("⚠️ Pastikan GEMINI_API_KEY sudah benar di Secrets!")
    st.stop()

# --- 4. SIDEBAR (HISTORY) ---
with st.sidebar:
    st.title("📁 Projects")
    if st.button("➕ Project Baru", use_container_width=True):
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
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

if "current_sid" not in st.session_state or st.session_state.current_sid is None:
    if sessions: st.session_state.current_sid = sessions[0][0]
    else:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 5. TAMPILAN UTAMA ---
st.title("🎨 Gemini Visual Studio")

c = conn.cursor()
c.execute("SELECT type, prompt, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
for r_type, r_p, r_url in c.fetchall():
    with st.container(border=True):
        st.write(f"**[{r_type.upper()}]** {r_p}")
        # Menampilkan gambar dengan penanganan error sederhana
        st.image(r_url, use_container_width=True, caption="AI Generated Result")

# --- 6. LOGIKA GENERATOR ---
st.write("---")
if prompt := st.chat_input("Apa yang ingin kamu buat?"):
    st.session_state.active_p = prompt

if "active_p" in st.session_state and st.session_state.active_p:
    st.info(f"Target: **{st.session_state.active_p}**")
    c1, c2 = st.columns(2)

    def generate_visual(mode_type):
        with st.spinner(f"Gemini sedang merancang {mode_type}..."):
            try:
                # 1. Gemini membuat prompt bahasa inggris yang sangat spesifik
                resp = model.generate_content(f"Detailed image prompt for: {st.session_state.active_p}. English only, one paragraph, descriptive, no quotes.")
                raw_text = resp.text.strip()
                
                # 2. MEMBERSIHKAN PROMPT (Menghapus karakter non-alfanumerik agar URL tidak pecah)
                clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', raw_text)
                encoded_prompt = urllib.parse.quote(clean_text)
                
                # 3. URL BUILDER (Gunakan model 'flux' yang lebih stabil)
                seed = random.randint(0, 999999)
                final_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux"
                
                # 4. SAVE & REFRESH
                c.execute("INSERT INTO results (session_id, type, prompt, output_url, timestamp) VALUES (?,?,?,?,?)",
                          (st.session_state.current_sid, mode_type, st.session_state.active_p, final_url, datetime.now().strftime("%H:%M")))
                c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (st.session_state.active_p[:15], st.session_state.current_sid))
                conn.commit()
                st.session_state.active_p = None
                st.rerun()
            except Exception as e:
                st.error(f"Gagal memproses visual: {e}")

    with c1:
        if st.button("🖼️ Generate Image", use_container_width=True):
            generate_visual("image")
    with c2:
        if st.button("🎥 Generate Video (Visual)", use_container_width=True):
            generate_visual("video")
