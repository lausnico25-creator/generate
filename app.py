import streamlit as st
import sqlite3
import google.generativeai as genai
import time
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Studio Gemini Enhanced", page_icon="🤖", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('ai_studio_gemini.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, 
                  type TEXT, prompt TEXT, expanded_prompt TEXT, output_url TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONFIGURASI GEMINI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("Pastikan GEMINI_API_KEY sudah terpasang di Secrets!")
    st.stop()

# --- 4. FUNGSI GEMINI UNTUK OPTIMASI PROMPT ---
def expand_prompt(user_prompt, target_type):
    instruction = f"Ubah prompt singkat ini menjadi prompt yang sangat detail untuk AI {target_type} Generator. Gunakan bahasa Inggris agar hasil lebih akurat. Balas HANYA dengan prompt barunya saja."
    response = model.generate_content(f"{instruction}\n\nUser Prompt: {user_prompt}")
    return response.text

# --- 5. SIDEBAR RIWAYAT (Sama seperti Tutor Korea) ---
with st.sidebar:
    st.title("🤖 AI Manager")
    if st.button("➕ Project Baru", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()

    st.write("---")
    c = conn.cursor()
    c.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    sessions = c.fetchall()
    for s_id, s_title in sessions:
        col_side, col_del = st.columns([4, 1])
        with col_side:
            if st.button(f"📁 {s_title}", key=f"s_{s_id}", use_container_width=True):
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
    if sessions: st.session_state.current_sid = sessions[0][0]
    else:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 7. TAMPILAN UTAMA ---
st.title("🚀 Gemini-Powered Studio")

# Tampilkan history dari database
c = conn.cursor()
c.execute("SELECT type, prompt, expanded_prompt, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
results = c.fetchall()

for r_type, r_p, r_exp, r_url in results:
    with st.chat_message("assistant" if r_type == "image" else "user"):
        st.write(f"**Prompt Asli:** {r_p}")
        with st.expander("Lihat Prompt yang Dioptimasi Gemini"):
            st.caption(r_exp)
        if r_type == "image": 
            st.image(r_url, caption="Hasil Gambar", use_container_width=True)
        else: 
            st.video(r_url)

# --- 8. INPUT AREA (PERBAIKAN LOGIKA) ---
st.write("---")
# Menggunakan chat_input sebagai pemicu utama
if user_input := st.chat_input("Deskripsikan ide visualmu di sini..."):
    # Simpan input ke session state agar tidak hilang saat tombol ditekan
    st.session_state.temp_prompt = user_input

# Jika ada prompt yang baru saja dimasukkan, tampilkan pilihan tombol
if "temp_prompt" in st.session_state and st.session_state.temp_prompt:
    st.info(f"Prompt aktif: **{st.session_state.temp_prompt}**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🖼️ Buat Gambar Sekarang", use_container_width=True):
            with st.spinner("Gemini sedang mempercantik prompt gambar..."):
                optimized = expand_prompt(st.session_state.temp_prompt, "Image")
                # Simulasi API (Ganti dengan API Key asli jika sudah ada)
                img_url = "https://picsum.photos/600/400" 
                
                c.execute("INSERT INTO results (session_id, type, prompt, expanded_prompt, output_url, timestamp) VALUES (?,?,?,?,?,?)",
                          (st.session_state.current_sid, "image", st.session_state.temp_prompt, optimized, img_url, datetime.now().strftime("%H:%M")))
                
                # Update Judul Sesi jika masih default
                c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (st.session_state.temp_prompt[:15], st.session_state.current_sid))
                conn.commit()
                
                # Bersihkan prompt sementara dan refresh
                st.session_state.temp_prompt = None
                st.rerun()

    with col2:
        if st.button("🎬 Buat Video Sekarang", use_container_width=True):
            with st.spinner("Gemini sedang merancang konsep video..."):
                optimized = expand_prompt(st.session_state.temp_prompt, "Video")
                vid_url = "https://www.w3schools.com/html/mov_bbb.mp4"
                
                c.execute("INSERT INTO results (session_id, type, prompt, expanded_prompt, output_url, timestamp) VALUES (?,?,?,?,?,?)",
                          (st.session_state.current_sid, "video", st.session_state.temp_prompt, optimized, vid_url, datetime.now().strftime("%H:%M")))
                
                c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", (st.session_state.temp_prompt[:15], st.session_state.current_sid))
                conn.commit()
                
                st.session_state.temp_prompt = None
                st.rerun()
