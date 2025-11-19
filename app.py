import streamlit as st
import os
import requests
import uuid
import base64
from io import BytesIO
from docx import Document
import pdfplumber

# -------------------------------
#  CONFIG
# -------------------------------
endpoint = os.getenv("https://api.cognitive.microsofttranslator.com")
key = os.getenv("4oyZQbx5UMvZbvvQIrML6ERBSwDcKEioD7740R9fSuN4F0SZ2eUXJQQJ99BKAC3pKaRXJ3w3AAAbACOGiFDZ")
region = os.getenv("eastasia")

if not key or not region:
    st.error("⚠️ Azure Translator environment variables are missing. Please set AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_REGION.")
    st.stop()

headers = {
    "Ocp-Apim-Subscription-Key": key,
    "Ocp-Apim-Subscription-Region": region,
    "Content-type": "application/json",
    "X-ClientTraceId": str(uuid.uuid4())
}

# -------------------------------
#  LANGUAGE LIST
# -------------------------------
LANGUAGES = {
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-Hans",
    "Chinese (Traditional)": "zh-Hant",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Turkish": "tr",
    "Urdu": "ur"
}

# -------------------------------
#  FUNCTIONS
# -------------------------------
def translate_text(text, to_lang):
    url = f"{endpoint}/translate?api-version=3.0&to={to_lang}"
    body = [{"text": text}]
    response = requests.post(url, headers=headers, json=body)
    return response.json()[0]["translations"][0]["text"]


def text_to_speech(text, lang):

    voice_map = {
        "en": "en-US-AriaNeural",
        "ur": "ur-PK-AsadNeural",
        "pa": "pa-IN-GeetaNeural",
        "ar": "ar-DZ-AminaNeural",
        "hi": "hi-IN-MadhurNeural",
        "tr": "tr-TR-EmelNeural",
        "es": "es-ES-ElviraNeural"
    }

    voice = voice_map.get(lang, "en-US-AriaNeural")

    tts_endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    tts_headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm"
    }

    ssml = f"""
    <speak version='1.0' xml:lang='{lang}'>
        <voice xml:lang='{lang}' xml:gender='Female' name='{voice}'>{text}</voice>
    </speak>
    """

    audio_response = requests.post(tts_endpoint, headers=tts_headers, data=ssml.encode('utf-8'))
    audio_base64 = base64.b64encode(audio_response.content).decode("utf-8")
    return audio_base64


def speech_to_text(audio_bytes, lang):

    stt_endpoint = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    stt_headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "audio/wav"
    }
    params = {"language": lang}

    response = requests.post(stt_endpoint, headers=stt_headers, params=params, data=audio_bytes)
    result = response.json()
    return result.get("DisplayText", "")


def translate_file(uploaded, lang):
    ext = uploaded.name.lower()

    if ext.endswith(".txt"):
        text = uploaded.read().decode("utf-8")
        return translate_text(text, lang)

    if ext.endswith(".docx"):
        doc = Document(uploaded)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        return translate_text(full_text, lang)

    if ext.endswith(".pdf"):
        with pdfplumber.open(uploaded) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        return translate_text(text, lang)

    return "Unsupported file type."


# -------------------------------
#  STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="🌍 Azure Translator — Full App", layout="wide")
st.title("🌍 Azure Translator (All Features Enabled)")

tab1, tab2, tab3, tab4 = st.tabs(["🔤 Text", "🎤 Speech ↔ Text", "📄 File Translation", "💬 Chat Mode"])

# -------------------------------
#  TAB 1: TEXT TRANSLATION
# -------------------------------
with tab1:
    st.subheader("🔤 Text Translation")

    text = st.text_area("Enter text", "")
    to_lang = st.selectbox("Translate to", list(LANGUAGES.keys()))
    to_lang_code = LANGUAGES[to_lang]

    if st.button("Translate Text"):
        translated = translate_text(text, to_lang_code)
        st.success("Translation:")
        st.write(translated)

        audio64 = text_to_speech(translated, to_lang_code)
        st.audio(base64.b64decode(audio64), format="audio/wav")

# -------------------------------
#  TAB 2: SPEECH-TO-TEXT & TTS
# -------------------------------
with tab2:
    st.subheader("🎤 Speech to Text + Translation")

    to_lang = st.selectbox("Translate speech into", list(LANGUAGES.keys()), key="speech_trans")
    to_lang_code = LANGUAGES[to_lang]

    audio_file = st.file_uploader("Upload a WAV audio file", type=["wav"])

    if audio_file:
        st.audio(audio_file)

    if st.button("Convert Speech"):
        if audio_file:
            recognized = speech_to_text(audio_file.read(), "en-US")
            translated = translate_text(recognized, to_lang_code)

            st.write("**Speech Recognized:**", recognized)
            st.write("**Translated:**", translated)

            audio64 = text_to_speech(translated, to_lang_code)
            st.audio(base64.b64decode(audio64), format="audio/wav")
        else:
            st.error("Please upload an audio file.")

# -------------------------------
#  TAB 3: FILE TRANSLATION
# -------------------------------
with tab3:
    st.subheader("📄 File Translator (PDF / DOCX / TXT)")

    file = st.file_uploader("Upload File", type=["pdf", "docx", "txt"])
    to_lang = st.selectbox("Translate file into", list(LANGUAGES.keys()), key="file_trans")
    to_lang_code = LANGUAGES[to_lang]

    if st.button("Translate File"):
        if file:
            translated = translate_file(file, to_lang_code)
            st.success("Translated Output:")
            st.write(translated)
        else:
            st.error("Upload a file first.")

# -------------------------------
#  TAB 4: CHAT MODE
# -------------------------------
with tab4:
    st.subheader("💬 Chat Translator")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    message = st.text_input("Your Message")
    lang = st.selectbox("Translate into", list(LANGUAGES.keys()), key="chat_trans")
    lang_code = LANGUAGES[lang]

    if st.button("Send"):
        translated = translate_text(message, lang_code)

        st.session_state.chat.append(("You", message))
        st.session_state.chat.append(("Translated", translated))

    for sender, msg in st.session_state.chat:
        st.write(f"**{sender}:** {msg}")
