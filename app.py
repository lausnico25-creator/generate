import streamlit as st
import sqlite3
import google.generativeai as genai
from openai import OpenAI
import time
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Creative Studio Pro", page_icon="🚀", layout="wide")

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('ai_studio_v2.db', check_same_thread=False)
    c = conn.cursor()
    # Tabel untuk kategori riwayat (sidebar)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)''')
    # Tabel untuk menyimpan hasil generate
    c.execute('''CREATE TABLE IF NOT EXISTS results 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, 
                  type TEXT, prompt TEXT, expanded_prompt TEXT, output_url TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. KONFIGURASI API ---
# Ambil dari st.secrets (Jika di Streamlit Cloud) atau isi manual untuk tes
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "MASUKKAN_KEY_GEMINI_DISINI")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "MASUKKAN_KEY_OPENAI_DISINI")

# Inisialisasi AI
try:
    genai.configure(api_key=GEMINI_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    client_openai = OpenAI(api_key=OPENAI_KEY)
except Exception as e:
    st.error(f"Kesalahan Konfigurasi API: {e}")

# --- 4. FUNGSI LOGIKA AI ---
def expand_prompt(user_prompt, target_type):
    """Menggunakan Gemini untuk memperdetail prompt sebelum dikirim ke Generator"""
    try:
        instruction = (
            f"Bertindaklah sebagai ahli prompt engineering untuk AI {target_type}. "
            f"Ubah prompt singkat ini menjadi deskripsi visual yang sangat detail, artistik, dan dalam bahasa Inggris. "
            f"Jangan berikan penjelasan, hanya berikan prompt hasil akhirnya saja."
        )
        response = gemini_model.generate_content(f"{instruction}\n\nPrompt User: {user_prompt}")
        return response.text
    except:
        return user_prompt # Fallback jika Gemini gagal

# --- 5. SIDEBAR (RIWAYAT & SETTINGS) ---
with st.sidebar:
    st.title("⚙️ AI History")
    if st.button("➕ Mulai Project Baru", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid
        st.rerun()

    st.divider()
    
    # Menampilkan daftar riwayat
    c = conn.cursor()
    c.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    all_sessions = c.fetchall()
    
    for s_id, s_title in all_sessions:
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

# --- 6. PENGECEKAN SESI AKTIF ---
if "current_sid" not in st.session_state or st.session_state.current_sid is None:
    if all_sessions:
        st.session_state.current_sid = all_sessions[0][0]
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = conn.cursor()
        c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", ("Project Baru", now))
        conn.commit()
        st.session_state.current_sid = c.lastrowid

# --- 7. TAMPILAN UTAMA ---
st.title("🎨 AI Creative Studio")
st.write(f"Sesi Aktif ID: `{st.session_state.current_sid}`")

# Tampilkan Hasil yang sudah ada di Database untuk sesi ini
c = conn.cursor()
c.execute("SELECT type, prompt, expanded_prompt, output_url FROM results WHERE session_id = ?", (st.session_state.current_sid,))
history_results = c.fetchall()

for r_type, r_p, r_exp, r_url in history_results:
    with st.container(border=True):
        st.write(f"**Prompt:** {r_p}")
        with st.expander("Lihat Prompt Optimasi Gemini"):
            st.caption(r_exp)
        
        if r_type == "image":
            st.image(r_url, caption="Hasil Gambar AI", use_container_width=True)
        else:
            st.video(r_url)
        st.divider()

# --- 8. INPUT AREA ---
st.write("---")
# Gunakan chat_input agar tampilannya modern
if user_input := st.chat_input("Contoh: Pesawat terbang di atas gunung es..."):
    st.session_state.active_prompt = user_input

# Jika ada prompt yang baru saja diketik, munculkan pilihan tombol
if "active_prompt" in st.session_state and st.session_state.active_prompt:
    st.info(f"Prompt siap diproses: **{st.session_state.active_prompt}**")
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("🖼️ Generate Image (DALL-E 3)", use_container_width=True):
            with st.spinner("Gemini sedang berpikir & DALL-E sedang melukis..."):
                # 1. Optimasi dengan Gemini
                detailed_prompt = expand_prompt(st.session_state.active_prompt, "Image Generator")
                
                try:
                    # 2. Panggil API DALL-E 3 yang ASLI
                    response = client_openai.images.generate(
                        model="dall-e-3",
                        prompt=detailed_prompt,
                        n=1,
                        size="1024x1024"
                    )
                    final_url = response.data[0].url
                    
                    # 3. Simpan ke DB
                    c.execute("INSERT INTO results (session_id, type, prompt, expanded_prompt, output_url, timestamp) VALUES (?,?,?,?,?,?)",
                              (st.session_state.current_sid, "image", st.session_state.active_prompt, detailed_prompt, final_url, datetime.now().strftime("%H:%M")))
                    
                    # Update Judul Sesi agar tidak 'Project Baru' terus
                    c.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'Project Baru'", 
                              (st.session_state.active_prompt[:15], st.session_state.current_sid))
                    conn.commit()
                    
                    st.session_state.active_prompt = None # Reset input
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal generate gambar: {e}")

    with btn_col2:
        if st.button("🎥 Generate Video", use_container_width=True):
            # Catatan: OpenAI belum merilis API Sora secara umum. 
            # Di sini kita berikan pesan edukatif atau bisa dihubungkan ke Replicate jika kamu mau.
            st.warning("API Video (seperti Sora) belum tersedia untuk publik secara luas. Gunakan API Replicate/Luma untuk integrasi video asli.")
            st.info("Tombol ini sudah siap, tinggal menunggu API Video pilihanmu dimasukkan.")
