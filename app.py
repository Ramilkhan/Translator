import streamlit as st
import requests
import uuid

# -------------------------------
#  Azure Translator Credentials
# -------------------------------
AZURE_TRANSLATOR_KEY = "4oyZQbx5UMvZbvvQIrML6ERBSwDcKEioD7740R9fSuN4F0SZ2eUXJQQJ99BKAC3pKaRXJ3w3AAAbACOGiFDZ"
AZURE_TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"
AZURE_TRANSLATOR_REGION = "eastasia"

# -------------------------------
#  Supported Languages
# -------------------------------
LANGUAGES = {
    "Auto Detect": "",
    "English": "en",
    "Urdu": "ur",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-Hans",
    "Chinese (Traditional)": "zh-Hant",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Spanish": "es",
    "Turkish": "tr",
    "Korean": "ko",
    "Japanese": "ja",
    "Russian": "ru",
    "Italian": "it",
    "Portuguese": "pt",
    "Persian": "fa",
    "Indonesian": "id",
    "Malay": "ms",
    "Thai": "th",
    "Pashto": "ps",
    "Bengali": "bn",
    "Punjabi": "pa",
}

# -------------------------------
#  Translation Function
# -------------------------------
def translate_text(text, to_lang="en", from_lang=None):
    path = "/translate?api-version=3.0"

    if from_lang:
        path += f"&from={from_lang}"

    path += f"&to={to_lang}"

    url = AZURE_TRANSLATOR_ENDPOINT + path

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4())
    }

    body = [{"text": text}]
    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        st.error(f"API Error: {response.text}")
        return None

    result = response.json()
    return result[0]["translations"][0]["text"]

# -------------------------------
#  Streamlit UI
# -------------------------------
st.set_page_config(page_title="Azure Translator", page_icon="🌐")

st.title("🌐 Azure Translator App")
st.write("Translate text easily using Azure Cognitive Services.")

input_text = st.text_area("Enter text to translate:")

col1, col2 = st.columns(2)

with col1:
    from_lang_name = st.selectbox("From Language", list(LANGUAGES.keys()))
    from_lang_code = LANGUAGES[from_lang_name] if LANGUAGES[from_lang_name] else None

with col2:
    to_lang_name = st.selectbox("To Language", list(LANGUAGES.keys())[1:])  # skip auto detect
    to_lang_code = LANGUAGES[to_lang_name]

if st.button("Translate"):
    if input_text.strip() == "":
        st.warning("Please enter text to translate.")
    else:
        translation = translate_text(input_text, to_lang_code, from_lang_code)

        if translation:
            st.subheader("🔁 Translated Text:")
            st.success(translation)
