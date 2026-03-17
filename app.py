import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Gemini Creative Studio", page_icon="♊", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('gemini_studio.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, type TEXT, prompt TEXT, ai_response TEXT, output_url TEXT, timestamp TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONEKSI API GEMINI ---
try:
    # Cukup satu Key ini saja!
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("⚠️ Masukkan GEMINI_API_KEY di Secrets Streamlit kamu!")
    st.stop()

# --- 4. SIDEBAR (RIWAYAT) ---
with st.sidebar:
    st.title("♊ Gemini History")
    if st.button("➕ Percakapan Baru", use_container_width=True):
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

# --- 5. TAMPILAN UTAMA ---
st.title("♊ Gemini AI Creative Studio")

# Load history
c = conn.cursor()
c.execute("SELECT type, prompt, ai_response, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
for r_type, r_p, r_ai, r_url in c.fetchall():
    with st.chat_message("user"):
        st.write(r_p)
    with st.chat_message("assistant"):
        st.write(r_ai)
        if r_url:
            st.image(r_url, use_container_width=True)

# --- 6. LOGIKA PROSES ---
if prompt := st.chat_input("Apa yang ingin kamu buat hari ini?"):
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Gemini sedang memproses..."):
            # Minta Gemini membuat deskripsi teknis
            response = model.generate_content(
                f"Kamu adalah AI kreatif. User ingin: {prompt}. "
                "Berikan penjelasan singkat tentang apa yang akan kamu buat dalam Bahasa Indonesia, "
                "lalu berikan satu baris terakhir berisi 'PROMPT_TEKNIS: [deskripsi dalam bahasa inggris]'."
            )
            full_text = response.text
            
            # Pisahkan penjelasan dengan prompt teknis untuk gambar
            if "PROMPT_TEKNIS:" in full_text:
                penjelasan = full_text.split("PROMPT_TEKNIS:")[0].strip()
                technical = full_text.split("PROMPT_TEKNIS:")[1].strip()
                
                # Menggunakan engine visual (gratis & stabil)
                encoded_p = urllib.parse.quote(technical)
                img_url = f"https://pollinations.ai/p/{encoded_p}?width=1024&height=1024&model=flux"
            else:
                penjelasan = full_text
                img_url = None

            st.write(penjelasan)
            if img_url:
                st.image(img_url, use_container_width=True)

            # Simpan ke DB
            c.execute("INSERT INTO results (session_id, type, prompt, ai_response, output_url, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_sid, "image", prompt, penjelasan, img_url, datetime.now().strftime("%H:%M")))
            
            # Update Judul Sidebar
            c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (prompt[:15], st.session_state.current_sid))
            conn.commit()
