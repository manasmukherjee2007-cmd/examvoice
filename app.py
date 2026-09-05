import os
import re
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
RIME_API_KEY = os.getenv("RIME_API_KEY")
RIME_API_URL = "https://users.rime.ai/v1/rime-tts"  # Standard Rime API endpoint

st.set_page_config(
    page_title="ExamVoice - Audio Reader for Visually Impaired Students",
    page_icon="🎙️",
    layout="wide"
)

# --- HELPER FUNCTIONS ---
def normalize_text_for_ear(text: str) -> str:
    """
    Transforms raw text with dense alphanumeric strings into clear,
    spaced-out representations for accessible speech delivery.
    Example: CS21B045 -> C. S. 2. 1. B. 0. 4. 5.
    """
    def format_code(match):
        code = match.group(0)
        # Space out individual characters with periods for pauses
        return " " + ". ".join(list(code)) + ". "

    # Pattern matches mixed alphanumeric sequences like PNR4521987663 or CS21B045
    pattern = r'\b(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*[0-9])[A-Za-z0-9]{4,}\b'
    normalized = re.sub(pattern, format_code, text)
    return normalized

def generate_rime_speech(text: str, model: str = "coda", speaker: str = "masonry", speed_alpha: float = 1.0) -> bytes:
    """Calls the Rime API to generate MP3/WAV audio bytes."""
    if not RIME_API_KEY:
        st.error("RIME_API_KEY is missing! Check your .env file or environment variables.")
        return None

    headers = {
        "Authorization": f"Bearer {RIME_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "audio/mp3"
    }

    payload = {
        "text": text,
        "speaker": speaker,
        "model": model,
        "speedAlpha": speed_alpha
    }

    try:
        response = requests.post(RIME_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Rime API Error ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- STREAMLIT UI ---
st.title("🎙️ ExamVoice")
st.caption("A voice-native application solving muddled speech for hall tickets and PNR identifiers.")

# Sidebar Controls
st.sidebar.header("Rime Engine Settings")
speaker_id = st.sidebar.text_input("Speaker ID", value="astra")
model_id = st.sidebar.selectbox("Model", ["coda", "mist"], index=0)
playback_speed = st.sidebar.slider("Speech Speed (speedAlpha)", min_value=0.5, max_value=1.2, value=0.85, step=0.05)

# Main Input Section
st.subheader("Document / Hall-Ticket Content")
sample_text = (
    "Welcome student. Your allocated seat is at Center Code PNR4521987663. "
    "Your Roll Number is CS21B045. Please report by 08:30 AM."
)
input_text = st.text_area("Enter text containing exam/PNR codes:", value=sample_text, height=120)

if st.button("Generate & Compare Delivery", type="primary"):
    if not input_text.strip():
        st.warning("Please enter some text first.")
    else:
        # Step 1: Compute normalized version
        normalized_text = normalize_text_for_ear(input_text)
        
        st.markdown("---")
        col1, col2 = st.columns(2)

        # Baseline Audio
        with col1:
            st.warning("❌ Baseline TTS (Default Unformatted Input)")
            st.caption("Standard TTS blurts alphanumeric codes together quickly, making them unreadable.")
            st.text_area("Raw Sent Text:", value=input_text, height=100, disabled=True)
            
            with st.spinner("Generating baseline audio..."):
                raw_audio = generate_rime_speech(
                    text=input_text, 
                    model=model_id, 
                    speaker=speaker_id, 
                    speed_alpha=1.0
                )
            if raw_audio:
                st.audio(raw_audio, format="audio/mp3")

        # ExamVoice Controlled Audio
        with col2:
            st.success("✅ ExamVoice + Rime (Controlled Phonetic Delivery)")
            st.caption("Normalized punctuation and pacing ensures crystal-clear ear readability.")
            st.text_area("Normalized Sent Text:", value=normalized_text, height=100, disabled=True)
            
            with st.spinner("Generating optimized ExamVoice audio..."):
                opt_audio = generate_rime_speech(
                    text=normalized_text, 
                    model=model_id, 
                    speaker=speaker_id, 
                    speed_alpha=playback_speed
                )
            if opt_audio:
                st.audio(opt_audio, format="audio/mp3")
                
                # Save optimized audio locally for evidence submission
                with open("examvoice_evidence.mp3", "wb") as f:
                    f.write(opt_audio)
                st.info("Saved 'examvoice_evidence.mp3' locally for your hackathon submission package!")

st.markdown("---")
st.markdown("**Hackathon Acceptance Test Note:** This test demonstrates how ExamVoice addresses *Pronunciation & Controlled Delivery* by inserting structured pauses and adjusting `speedAlpha` for ear-accessibility.")
import os
import requests
import streamlit as st
from pypdf import PdfReader
import docx

# Streamlit Page Config
st.set_page_config(page_title="ExamVoice AI", page_icon="🎙️")
st.title("🎙️ ExamVoice AI")
st.caption("Upload documents and listen via Rime AI TTS")

# API Configuration
# Best practice: Add RIME_API_KEY to your Streamlit Secrets or environment variables
RIME_API_KEY = st.secrets.get("RIME_API_KEY") or os.getenv("RIME_API_KEY")

if not RIME_API_KEY:
    RIME_API_KEY = st.sidebar.text_input("Enter Rime API Key", type="password")

# Voice selection sidebar
speaker = st.sidebar.selectbox("Select Speaker", ["celeste", "luna", "cove", "mist"])
speed = st.sidebar.slider("Speed (Alpha)", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

# Document extraction helper
def extract_text(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        text = "\n".join([p.text for p in doc.paragraphs])
    elif uploaded_file.name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8")
    return text.strip()

# Rime AI TTS API caller
def generate_rime_speech(text, speaker, speed, api_key):
    url = "https://users.rime.ai/v1/rime-tts"
    headers = {
        "Accept": "audio/mp3",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "modelId": "coda",
        "speaker": speaker,
        "speedAlpha": speed,
        "samplingRate": 22050,
        "pauseBetweenBrackets": True,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    return response

# Main UI
uploaded_file = st.file_uploader("Upload a document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

if uploaded_file:
    extracted_text = extract_text(uploaded_file)
    
    if not extracted_text:
        st.error("No readable text found in the uploaded file.")
    else:
        # Allow user to preview or edit the text before generating audio
        spoken_text = st.text_area("Text to be read aloud:", value=extracted_text[:1500], height=200)
        st.info("Note: Showing the first segment to prevent exceeding API payload limits.")

        if st.button("Generate Audio"):
            if not RIME_API_KEY:
                st.error("Please provide a valid Rime API Key.")
            else:
                with st.spinner("Generating speech via Rime AI..."):
                    try:
                        resp = generate_rime_speech(spoken_text, speaker, speed, RIME_API_KEY)
                        if resp.status_code == 200:
                            st.success("Audio generated successfully!")
                            st.audio(resp.content, format="audio/mp3")
                            st.download_button(
                                label="Download MP3",
                                data=resp.content,
                                file_name="exam_voice_audio.mp3",
                                mime="audio/mp3",
                            )
                        else:
                            st.error(f"Rime API Error ({resp.status_code}): {resp.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Request failed: {e}")