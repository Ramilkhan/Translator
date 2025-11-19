import streamlit as st
import requests
import os
import uuid
import json

# -------------------------------
#  Azure Translator Settings
# -------------------------------
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")

if not AZURE_TRANSLATOR_KEY or not AZURE_TRANSLATOR_REGION:
    st.error("⚠️ Azure Translator environment variables are missing. "
             "Please set AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION.")
    st.stop()

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
st.write("Translate text using Azure Cognitive Services Translator API.")

input_text = st.text_area("Enter text to translate:")

col1, col2 = st.columns(2)
with col1:
    from_lang = st.text_input("From Language (optional)", placeholder="auto-detect")

with col2:
    to_lang = st.text_input("To Language", value="en")

if st.button("Translate"):
    if input_text.strip() == "":
        st.warning("Please enter text to translate.")
    else:
        translation = translate_text(input_text, to_lang, from_lang if from_lang else None)

        if translation:
            st.subheader("🔁 Translated Text:")
            st.success(translation)
