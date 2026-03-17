import streamlit as st
import sqlite3
import google.generativeai as genai
from openai import OpenAI
import time
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Studio Pro", page_icon="🎨", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('studio_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, 
                  type TEXT, prompt TEXT, expanded_prompt TEXT, output_url TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONEKSI API (MENGGUNAKAN SECRETS) ---
try:
    # Membaca key dari Streamlit Cloud Secrets
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
    
    genai.configure(api_key=GEMINI_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    client_openai = OpenAI(api_key=OPENAI_KEY)
except Exception as e:
    st.error("⚠️ API Key Error: Pastikan GEMINI_API_KEY dan OPENAI_API_KEY sudah diisi di 'Settings > Secrets' di dashboard Streamlit.")
    st.stop()

# --- 4. FUNGSI OPTIMASI PROMPT ---
def get_better_prompt(user_text, mode):
    try:
        prompt_style = f"Detailed {mode} generation prompt, cinematic, high resolution, professional lighting, 8k."
        response = gemini_model.generate_content(f"{prompt_style}\n\nUser Input: {user_text}")
        return response.text
    except:
        return user_text

# --- 5. SIDEBAR (RIWAYAT) ---
with st.sidebar:
    st.title("📁 History")
    if st.button("➕ Chat Baru", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Percakapan Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()

    st.write("---")
    c = conn.cursor()
    c.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    sessions = c.fetchall()
    
    for s_id, s_title in sessions:
        col_chat, col_del = st.columns([4, 1])
        with col_chat:
            if st.button(f"📄 {s_title}", key=f"s_{s_id}", use_container_width=True):
                st.session_state.current_sid = s_id
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{s_id}"):
                c.execute("DELETE FROM sessions WHERE id = ?", (s_id,))
                c.execute("DELETE FROM results WHERE session_id = ?", (s_id,))
                conn.commit()
                st.session_state.current_sid = None
                st.rerun()

# --- 6. LOGIKA SESI ---
if "current_sid" not in st.session_state or st.session_state.current_sid is None:
    if sessions:
        st.session_state.current_sid = sessions[0][0]
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Percakapan Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 7. AREA TAMPILAN UTAMA ---
st.title("🎓 AI Creative Studio")

# Tampilkan isi database untuk sesi saat ini
c = conn.cursor()
c.execute("SELECT type, prompt, expanded_prompt, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
for r_type, r_p, r_exp, r_url in c.fetchall():
    with st.container(border=True):
        st.write(f"**Prompt:** {r_p}")
        if r_type == "image":
            st.image(r_url, use_container_width=True)
        else:
            st.video(r_url)
        with st.expander("Detail AI Prompt"):
            st.caption(r_exp)

# --- 8. BAGIAN INPUT ---
st.write("---")
if prompt := st.chat_input("Apa yang ingin kamu buat?"):
    st.session_state.last_prompt = prompt

if "last_prompt" in st.session_state and st.session_state.last_prompt:
    st.info(f"Siap memproses: **{st.session_state.last_prompt}**")
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("🖼️ Generate Image", use_container_width=True):
            with st.spinner("Menggambar..."):
                better_prompt = get_better_prompt(st.session_state.last_prompt, "Image")
                try:
                    res = client_openai.images.generate(
                        model="dall-e-3",
                        prompt=better_prompt,
                        n=1, size="1024x1024"
                    )
                    url = res.data[0].url
                    
                    c.execute("INSERT INTO results (session_id, type, prompt, expanded_prompt, output_url, timestamp) VALUES (?,?,?,?,?,?)",
                              (st.session_state.current_sid, "image", st.session_state.last_prompt, better_prompt, url, datetime.now().strftime("%H:%M")))
                    # Auto-update judul sidebar
                    c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Percakapan Baru'", (st.session_state.last_prompt[:15], st.session_state.current_sid))
                    conn.commit()
                    st.session_state.last_prompt = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with c2:
        if st.button("🎥 Generate Video", use_container_width=True):
            st.warning("Maaf, API Video Sora belum dibuka oleh OpenAI untuk publik. Tombol ini sudah siap dihubungkan jika API sudah rilis.")
