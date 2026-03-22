import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from streamlit_mic_recorder import speech_to_text
import os
import json
import time

# --- 1. ANAHTARLAR ---
GOOGLE_API_KEY = "AIzaSyB82uSgoPixO0xcuWmWxztlU0s0bIGO1Xc"
ELEVENLABS_API_KEY = "sk_bf3c6c09abbec997df73b1edeaaf0189b258428d57884c10"

genai.configure(api_key=GOOGLE_API_KEY)
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

MEMORY_FILE = "jarvis_memory_v3.json"

# JARVIS'E KİMLİĞİNİ HATIRLATIYORUZ
SYSTEM_INSTRUCTION = """
Sen JARVIS'sin. Gökhan'ın yüksek seviyeli teknik asistanısın. 
Gökhan; elektrik öğretmeni ve CNC/Mermer/Cam işleme uzmanıdır.
Karakterin: Tony Stark'ın asistanı gibi karizmatik, zeki ve teknik. 
Onunla konuşurken "Gökhan Bey" hitabını kullanabilirsin. 
H100 standı, 1200mm lazer makinesi ve mermer projelerini biliyorsun.
"""

st.set_page_config(page_title="JARVIS PRIME v3.3", page_icon="🎙️", layout="wide")

# --- 2. HAFIZA SİSTEMİ ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

# --- 3. DİNAMİK MODEL SEÇİMİ ---
@st.cache_resource
def get_jarvis_model():
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # En güncel modeli (flash) seçmeye çalış, yoksa ilkini al
    target_model = next((m for m in models if "flash" in m), models[0])
    return genai.GenerativeModel(model_name=target_model, system_instruction=SYSTEM_INSTRUCTION)

# --- 4. PROFESYONEL SESLENDİRME ---
def speak(text):
    try:
        audio = client.generate(
            text=text,
            voice="Antoni", # Profesyonel erkek sesi
            model="eleven_multilingual_v2"
        )
        with open("jarvis_speech.mp3", "wb") as f:
            for chunk in audio: f.write(chunk)
        st.audio("jarvis_speech.mp3", format="audio/mp3", autoplay=True)
    except Exception as e:
        st.warning("Ses sisteminde yoğunluk var, metin olarak yanıt veriyorum.")

# --- 5. ARAYÜZ VE SOHBET ---
st.title("🎙️ JARVIS PRIME: Atölye Paneli")

# Mesaj geçmişini ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Giriş Seçenekleri
with st.sidebar:
    st.header("Sistem Kontrol")
    if st.button("Hafızayı Sıfırla"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()
    st.info("Bellek Aktif: Jarvis projelerinizi hatırlıyor.")

# Sesli Giriş ve Metin Girişi
col1, col2 = st.columns([4, 1])
with col2:
    v_input = speech_to_text(language='tr', start_prompt="Dinle", stop_prompt="Tamam", key='jarvis_mic')
with col1:
    t_input = st.chat_input("Talimatınız?")

prompt = t_input or v_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geçmişle birlikte modeli çalıştır
    history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
               for m in st.session_state.messages[:-1]]

    try:
        model = get_jarvis_model()
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        # Belleği Dosyaya Yaz
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=4)
        
        # Sesi Çal
        speak(response.text)

    except Exception as e:
        if "429" in str(e):
            st.error("Gökhan Bey, kota doldu. Lütfen 30 saniye sonra tekrar deneyin.")
        else:
            st.error(f"Sistem Hatası: {e}")