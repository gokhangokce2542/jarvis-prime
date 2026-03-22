import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from streamlit_mic_recorder import speech_to_text
import os
import json

# --- 1. GÜVENLİ ANAHTAR YÖNETİMİ (KASA SİSTEMİ) ---
# Bu yapı, anahtarların sızdırılmasını ve iptal edilmesini engeller.
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
except Exception:
    st.error("Gökhan Bey, Secrets (Kasa) ayarları eksik!")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

MEMORY_FILE = "jarvis_memory_v3.json"

# --- 2. JARVIS KİŞİLİK VE ATÖLYE BİLGİSİ ---
SYSTEM_INSTRUCTION = """
Sen JARVIS'sin. Gökhan'ın profesyonel teknik asistanısın. 
Gökhan; elektrik öğretmeni ve CNC/Mermer/Cam işleme uzmanıdır.
Karakterin: Karizmatik, zeki ve teknik. Hitabın: "Gökhan Bey".
Projeler: H100 standı, 1200mm lazer ve mermer baş taşı projelerini biliyorsun.
"""

st.set_page_config(page_title="JARVIS PRIME v3.3", page_icon="🎙️", layout="wide")

# --- 3. AKILLI HAFIZA ---
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

# --- 4. MODEL SEÇİCİ (404 HATASI ÇÖZÜMÜ) ---
@st.cache_resource
def get_jarvis_model():
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = next((m for m in models if "flash" in m), models[0])
    return genai.GenerativeModel(model_name=target_model, system_instruction=SYSTEM_INSTRUCTION)

# --- 5. SESLENDİRME ---
def speak(text):
    try:
        audio = client.generate(text=text, voice="Antoni", model="eleven_multilingual_v2")
        with open("jarvis_speech.mp3", "wb") as f:
            for chunk in audio: f.write(chunk)
        st.audio("jarvis_speech.mp3", format="audio/mp3", autoplay=True)
    except:
        st.warning("Ses sistemi şu an yoğun, metinle devam ediyorum.")

# --- 6. ATÖLYE PANELİ ---
st.title("🎙️ JARVIS PRIME: Atölye Paneli")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

col1, col2 = st.columns([4, 1])
with col2:
    v_input = speech_to_text(language='tr', start_prompt="Dinle", stop_prompt="Tamam", key='jarvis_mic')
with col1:
    t_input = st.chat_input("Emredin Gökhan Bey...")

prompt = t_input or v_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        model = get_jarvis_model()
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                   for m in st.session_state.messages[:-1]]
        
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        
        with st.chat_message("assistant"): st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=4)
        
        speak(response.text)
    except Exception as e:
        st.error(f"Sistem Hatası: {e}")
