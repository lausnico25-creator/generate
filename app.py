import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Gemini Creative Studio", page_icon="♊", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('gemini_studio_v3.db', check_same_thread=False)
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
    st.error("⚠️ Masukkan GEMINI_API_KEY di Secrets!")
    st.stop()

# --- 4. SIDEBAR (SETTINGS & HISTORY) ---
with st.sidebar:
    st.title("⚙️ Settings")
    if st.button("➕ Project Baru", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()

    st.divider()
    st.subheader("History")
    c = conn.cursor()
    c.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    sessions = c.fetchall()
    
    for s_id, s_title in sessions:
        col_s, col_d = st.columns([4, 1])
        with col_s:
            if st.button(f"📁 {s_title}", key=f"s_{s_id}", use_container_width=True):
                st.session_state.current_sid = s_id
                st.rerun()
        with col_d:
            if st.button("🗑️", key=f"del_{s_id}"):
                c.execute("DELETE FROM sessions WHERE id = ?", (s_id,))
                c.execute("DELETE FROM results WHERE session_id = ?", (s_id,))
                conn.commit()
                st.session_state.current_sid = None
                st.rerun()

# --- 5. LOGIKA SESI ---
if "current_sid" not in st.session_state or st.session_state.current_sid is None:
    if sessions: st.session_state.current_sid = sessions[0][0]
    else:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 6. TAMPILAN UTAMA ---
st.title("🎨 Gemini Creative Studio")

# Load history hasil kerja
c = conn.cursor()
c.execute("SELECT type, prompt, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
for r_type, r_p, r_url in c.fetchall():
    with st.container(border=True):
        st.write(f"**[{r_type.upper()}] Prompt:** {r_p}")
        if r_type == "image":
            st.image(r_url, use_container_width=True)
        else:
            st.video(r_url)

# --- 7. INPUT AREA & TOMBOL ---
st.write("---")
user_input = st.chat_input("Apa yang ingin kamu buat?")

if user_input:
    st.session_state.active_prompt = user_input

if "active_prompt" in st.session_state and st.session_state.active_prompt:
    st.info(f"Pilih format untuk: **{st.session_state.active_prompt}**")
    col_img, col_vid = st.columns(2)

    with col_img:
        if st.button("🖼️ Generate Image", use_container_width=True):
            with st.spinner("Gemini sedang merancang gambar..."):
                # Minta Gemini membuat prompt teknis bahasa inggris
                response = model.generate_content(f"Create a high quality image prompt in English for: {st.session_state.active_prompt}. Provide ONLY the prompt.")
                tech_prompt = response.text
                
                # Buat URL Gambar (Engine Gratis)
                encoded = urllib.parse.quote(tech_prompt)
                img_url = f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&model=flux"
                
                # Simpan ke DB
                c.execute("INSERT INTO results (session_id, type, prompt, output_url, timestamp) VALUES (?,?,?,?,?)",
                          (st.session_state.current_sid, "image", st.session_state.active_prompt, img_url, datetime.now().strftime("%H:%M")))
                c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (st.session_state.active_prompt[:15], st.session_state.current_sid))
                conn.commit()
                st.session_state.active_prompt = None
                st.rerun()

    with col_vid:
        if st.button("🎥 Generate Video", use_container_width=True):
            # Placeholder Video (Karena API Video mayoritas berbayar)
            st.warning("Fitur Video sedang dalam pengembangan API.")
            # Contoh penggunaan video statis agar tidak error
            vid_url = "https://www.w3schools.com/html/mov_bbb.mp4"
            c.execute("INSERT INTO results (session_id, type, prompt, output_url, timestamp) VALUES (?,?,?,?,?)",
                      (st.session_state.current_sid, "video", st.session_state.active_prompt, vid_url, datetime.now().strftime("%H:%M")))
            conn.commit()
            st.session_state.active_prompt = None
            st.rerun()
