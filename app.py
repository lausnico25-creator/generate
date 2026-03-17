import streamlit as st
import sqlite3
import google.generativeai as genai
import urllib.parse
import random
import re
from datetime import datetime

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="Gemini Visual Studio", page_icon="♊", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect('gemini_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, type TEXT, prompt TEXT, url TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. API SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    st.error("API Key Gemini tidak ditemukan di Secrets!")
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("📁 Menu")
    if st.button("➕ Project Baru", use_container_width=True):
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title) VALUES (?)", ("Project Baru",))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()
    
    st.divider()
    c = conn.cursor()
    c.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    for s_id, s_title in c.fetchall():
        if st.button(f"📄 {s_title}", key=f"s_{s_id}", use_container_width=True):
            st.session_state.current_sid = s_id
            st.rerun()

if "current_sid" not in st.session_state:
    c = conn.cursor()
    c.execute("SELECT id FROM sessions ORDER BY id DESC LIMIT 1")
    res = c.fetchone()
    if res: st.session_state.current_sid = res[0]
    else:
        c.execute("INSERT INTO sessions (title) VALUES (?)", ("Project Baru",))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 5. MAIN UI ---
st.title("♊ Gemini Visual Studio")

# Tampilkan History
c = conn.cursor()
c.execute("SELECT type, prompt, url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
for r_type, r_p, r_url in c.fetchall():
    with st.container(border=True):
        st.write(f"**[{r_type}]** {r_p}")
        st.image(r_url, use_container_width=True)

# --- 6. GENERATOR LOGIC ---
st.write("---")
if user_input := st.chat_input("Ketik sesuatu... (Contoh: Kucing astronot)"):
    st.session_state.p_aktif = user_input

if "p_aktif" in st.session_state and st.session_state.p_aktif:
    st.info(f"Siap proses: **{st.session_state.p_aktif}**")
    col1, col2 = st.columns(2)

    def buat_visual(tipe):
        with st.spinner(f"Sedang membuat {tipe}..."):
            # A. Gemini bikin prompt inggris super simpel
            try:
                res = model.generate_content(f"Translate to simple English image description: {st.session_state.p_aktif}")
                eng_text = res.text.strip()
                # B. BERSIHKAN TOTAL (Hanya huruf dan spasi)
                clean_text = re.sub(r'[^a-zA-Z\s]', '', eng_text)
                final_prompt = clean_text.replace(" ", ",")
                
                # C. URL Generator
                random_id = random.randint(1, 999999)
                # Gunakan format URL yang lebih simpel
                img_url = f"https://pollinations.ai/p/{final_prompt}?width=1024&height=1024&seed={random_id}&nologo=true"
                
                # D. Simpan
                c.execute("INSERT INTO results (session_id, type, prompt, url) VALUES (?,?,?,?)",
                          (st.session_state.current_sid, tipe, st.session_state.p_aktif, img_url))
                c.execute("UPDATE sessions SET title = ? WHERE id = ?", (st.session_state.p_aktif[:15], st.session_state.current_sid))
                conn.commit()
                
                del st.session_state.p_aktif
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col1:
        if st.button("🖼️ Buat Gambar", use_container_width=True):
            buat_visual("IMAGE")
    with col2:
        if st.button("🎥 Buat Video (Visual)", use_container_width=True):
            buat_visual("VIDEO")
