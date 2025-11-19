"""
Streamlit Azure Translator app with:
- language dropdowns (auto-detect)
- speech-to-text (browser Web Speech API; copy transcript to Streamlit input)
- text-to-speech (browser SpeechSynthesis)
- file translation: PDF, DOCX, TXT
- chat-style UI
- copy translated text button (browser clipboard)
Requires user to provide Azure Translator Key & Region in sidebar (secure input).
"""

import streamlit as st
import requests
import uuid
import io
from typing import Optional, List

# file parsing libs
from PyPDF2 import PdfReader
import docx

st.set_page_config(page_title="Azure Translator — All Features", page_icon="🌐", layout="wide")

# ---------------------------
# Languages dictionary
# (trimmed but includes many common languages)
# ---------------------------
LANGUAGES = {
    "Auto Detect": "",
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese (Simplified)": "zh-Hans",
    "Chinese (Traditional)": "zh-Hant",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Urdu": "ur",
    "Hindi (Latin)": "hi-Latn",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Malay": "ms",
    "Persian / Farsi": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Russian": "ru",
    "Spanish": "es",
    "Swahili": "sw",
    "Thai": "th",
    "Turkish": "tr",
    "Vietnamese": "vi",
    "Pashto": "ps",
    "Burmese (Myanmar)": "my",
}

# ---------------------------
# Helpers: Azure Translate
# ---------------------------
def translate_text_azure(
    text: str,
    to_lang: str,
    from_lang: Optional[str],
    endpoint: str,
    key: str,
    region: str,
) -> Optional[str]:
    """
    Translate a single text string using Azure Translator REST API.
    Returns translated text or None on error.
    """
    if not key or not region or not endpoint:
        st.error("Azure Translator Key / Endpoint / Region not provided.")
        return None

    path = "/translate?api-version=3.0"
    if from_lang:
        path += f"&from={from_lang}"
    path += f"&to={to_lang}"

    url = endpoint.rstrip("/") + path
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    try:
        response = requests.post(url, headers=headers, json=[{"text": text}], timeout=20)
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

    if response.status_code != 200:
        st.error(f"Azure API error {response.status_code}: {response.text}")
        return None

    try:
        res_json = response.json()
        # Some responses include multiple translations; take first
        translated = res_json[0]["translations"][0]["text"]
        return translated
    except Exception as e:
        st.error(f"Failed to parse translation response: {e}")
        return None


# ---------------------------
# File text extractors
# ---------------------------
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text_pages: List[str] = []
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            try:
                text_pages.append(page.extract_text() or "")
            except Exception:
                # fallback: ignore page
                text_pages.append("")
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return "\n".join(text_pages)


def extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    text_list: List[str] = []
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for p in doc.paragraphs:
            text_list.append(p.text)
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
    return "\n".join(text_list)


def extract_text_from_txt_bytes(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return file_bytes.decode("latin-1", errors="ignore")


# ---------------------------
# UI Layout
# ---------------------------
st.title("🌐 Azure Translator — All Features")
st.markdown(
    """
Small note about Speech features:
- **Speech-to-text** uses your browser's built-in Speech Recognition (Web Speech API). Click **Start Recording** in the widget and copy the transcript into the input box.
- **Text-to-speech** uses the browser's speech synthesis (plays audio in your browser).
"""
)

# Sidebar: Azure credentials
with st.sidebar.expander("Azure Translator Settings (enter your key here)"):
    st.write("Enter Translator key, region and endpoint.")
    AZURE_TRANSLATOR_KEY = st.text_input("Translator Key (secret)", type="password")
    AZURE_TRANSLATOR_REGION = st.text_input("Region (e.g., eastasia, global)", value="eastasia")
    AZURE_TRANSLATOR_ENDPOINT = st.text_input(
        "Endpoint", value="https://api.cognitive.microsofttranslator.com"
    )
    st.caption("Do not paste production keys in public repos. Regenerate keys if exposed.")

# Main UI: left and right columns
left, right = st.columns((2, 3))

with left:
    st.subheader("Input")
    # Speech widget (browser-based)
    st.markdown("**Speech → Text (browser microphone)**")
    st.info(
        "Click Start Recording in the widget below. When speech is recognized, press 'Copy transcript' and then paste (Ctrl+V) into the 'Text to translate' box."
    )

    # HTML-based speech recognition widget:
    speech_widget_html = """
    <div style="border:1px solid #eee; padding:10px; border-radius:6px;">
      <div id="status">Status: idle</div>
      <textarea id="transcript" rows="6" style="width:100%;"></textarea>
      <div style="margin-top:6px;">
        <button id="start">Start Recording</button>
        <button id="stop" disabled>Stop</button>
        <button id="copy">Copy transcript</button>
      </div>
      <div style="font-size:12px; margin-top:6px; color:#666;">
        Uses browser Web Speech API (works in Chrome/Edge & some Chromium-based browsers).
      </div>
    </div>

    <script>
    const startBtn = document.getElementById('start');
    const stopBtn = document.getElementById('stop');
    const copyBtn = document.getElementById('copy');
    const statusDiv = document.getElementById('status');
    const transcriptTA = document.getElementById('transcript');

    // feature detect
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        statusDiv.innerText = "Status: Speech Recognition not supported in this browser.";
        startBtn.disabled = true;
    } else {
        const recog = new SpeechRecognition();
        recog.lang = 'en-US';
        recog.interimResults = true;
        recog.continuous = false;

        recog.onstart = () => {
            statusDiv.innerText = "Status: listening...";
            startBtn.disabled = true;
            stopBtn.disabled = false;
        };

        recog.onerror = (e) => {
            statusDiv.innerText = "Error: " + e.error;
            startBtn.disabled = false;
            stopBtn.disabled = true;
        };

        recog.onresult = (ev) => {
            let interim = '';
            let final = '';
            for (let i = ev.resultIndex; i < ev.results.length; ++i) {
                if (ev.results[i].isFinal) {
                    final += ev.results[i][0].transcript;
                } else {
                    interim += ev.results[i][0].transcript;
                }
            }
            transcriptTA.value = final + (interim ? '\\n(' + interim + ')' : '');
        };

        recog.onend = () => {
            statusDiv.innerText = "Status: stopped";
            startBtn.disabled = false;
            stopBtn.disabled = true;
        };

        startBtn.addEventListener('click', () => {
            try { recog.start(); } catch(e){ }
        });
        stopBtn.addEventListener('click', () => { recog.stop(); });
    }

    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(transcriptTA.value);
            copyBtn.innerText = 'Copied!';
            setTimeout(()=>copyBtn.innerText='Copy transcript', 1200);
        } catch (e) {
            alert('Clipboard copy failed: ' + e);
        }
    });
    </script>
    """
    st.components.v1.html(speech_widget_html, height=220, scrolling=True)

    st.markdown("---")
    text_to_translate = st.text_area("Text to translate", height=180, placeholder="Type or paste text here (or paste transcript from the widget)...")

    st.markdown("**File translation** (PDF, DOCX, TXT). The extracted text will be shown and translated.")
    uploaded_file = st.file_uploader("Upload PDF / DOCX / TXT", type=["pdf", "docx", "txt"])

    translate_button = st.button("Translate ▶️")

with right:
    st.subheader("Translator settings")
    from_lang_name = st.selectbox("From language", list(LANGUAGES.keys()), index=0)
    to_lang_name = st.selectbox("To language", list(LANGUAGES.keys())[1:], index=1)
    from_lang_code = LANGUAGES.get(from_lang_name) or None
    to_lang_code = LANGUAGES.get(to_lang_name)

    st.markdown("---")
    st.subheader("Chat-style conversation")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # list of (source, translation, from_lang, to_lang)

    # Conversation display
    def render_chat():
        for i, (src, tgt, f_lang, t_lang) in enumerate(reversed(st.session_state.chat_history[-20:])):
            st.markdown("---")
            st.markdown(f"**You ({f_lang or 'auto'}) → {t_lang}**")
            st.write(src)
            st.markdown("**Translation:**")
            st.success(tgt)
            # copy + speak buttons next to each translation
            # create two HTML buttons: copy and play
            html_buttons = f'''
            <div>
                <button onclick="navigator.clipboard.writeText(`{tgt.replace('`','\\`').replace('\\n','\\\\n')}`)">Copy</button>
                <button onclick="(function(t){{
                    const ut = new SpeechSynthesisUtterance(t);
                    // set lang if available
                    try{{ ut.lang = '{to_lang_code}';}}catch(e){}
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(ut);
                }})(`{tgt.replace('`','\\`').replace('\\n','\\\\n')}`)">Play</button>
            </div>
            '''
            st.components.v1.html(html_buttons, height=50)

    render_chat()

# ---------------------------
# Actions
# ---------------------------
if translate_button:
    # If a file was uploaded, extract text and translate
    source_texts = []

    if uploaded_file is not None:
        b = uploaded_file.read()
        file_type = uploaded_file.type.lower()
        st.info(f"Uploaded file: {uploaded_file.name} ({file_type}) — extracting text...")
        if uploaded_file.name.lower().endswith(".pdf"):
            extracted = extract_text_from_pdf_bytes(b)
        elif uploaded_file.name.lower().endswith(".docx"):
            extracted = extract_text_from_docx_bytes(b)
        else:
            extracted = extract_text_from_txt_bytes(b)

        if not extracted.strip():
            st.warning("No text could be extracted from the uploaded file.")
        else:
            st.subheader("Extracted Text (first 2000 chars)")
            st.write(extracted[:2000] + ("..." if len(extracted) > 2000 else ""))
            source_texts = [extracted]
    else:
        if not text_to_translate.strip():
            st.warning("Type text or upload a file before translating.")
            st.stop()
        source_texts = [text_to_translate]

    # For each source text, translate (if long, we do chunking by paragraphs)
    translations = []
    for s in source_texts:
        # simple chunking by paragraphs to avoid very long single API call
        paragraphs = [p for p in s.splitlines() if p.strip()]
        translated_full = []
        for p in paragraphs:
            translated = translate_text_azure(
                p,
                to_lang_code,
                from_lang_code,
                AZURE_TRANSLATOR_ENDPOINT,
                AZURE_TRANSLATOR_KEY,
                AZURE_TRANSLATOR_REGION,
            )
            if translated is None:
                translated = "[translation failed]"
            translated_full.append(translated)
        translations.append("\n".join(translated_full))

    # Add to chat history and show top result
    for src, tgt in zip(source_texts, translations):
        st.session_state.chat_history.append((src, tgt, from_lang_name, to_lang_name))

    st.success("Translation complete — scroll on the right to see the chat history.")

# Small helpful buttons for clearing chat or history
st.sidebar.markdown("---")
if st.sidebar.button("Clear conversation history"):
    st.session_state.chat_history = []
    st.sidebar.success("Cleared.")

# Inline text-to-speech for latest translation (render UI)
if st.session_state.chat_history:
    latest_src, latest_tgt, f_lang_name, t_lang_name = st.session_state.chat_history[-1]
    st.markdown("---")
    st.subheader("Latest translation (play & copy)")
    st.write(latest_tgt)

    # copy and play buttons using HTML (browser)
    buttons_html = f"""
    <div>
      <button onclick="navigator.clipboard.writeText(`{latest_tgt.replace('`','\\`').replace('\\n','\\\\n')}`)">Copy translation</button>
      <button onclick="(function(t){{
        const u = new SpeechSynthesisUtterance(t);
        try{{ u.lang = '{to_lang_code}'; }}catch(e){{}}
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      }})(`{latest_tgt.replace('`','\\`').replace('\\n','\\\\n')}`)">Play translation</button>
    </div>
    """
    st.components.v1.html(buttons_html, height=60)
