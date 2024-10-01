import streamlit as st
import speech_recognition as sr
import pronouncing
import tempfile
import os
import base64

# Function to transcribe audio
def transcribe_audio(file_path):
    r = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")
        return None

# Function to calculate phoneme score
def phoneme_score(ref_word, spoken_word):
    ref_phonemes = pronouncing.phones_for_word(ref_word)
    spoken_phonemes = pronouncing.phones_for_word(spoken_word)

    if not ref_phonemes or not spoken_phonemes:
        return 0

    ref_phoneme_list = ref_phonemes[0].split()
    spoken_phoneme_list = spoken_phonemes[0].split()

    matches = sum(1 for ref, spoken in zip(ref_phoneme_list, spoken_phoneme_list) if ref == spoken)
    return matches / max(len(ref_phoneme_list), len(spoken_phoneme_list))

# Function to evaluate pronunciation
def evaluate_pronunciation(reference_text, user_text):
    reference_words = reference_text.lower().split()
    user_words = user_text.lower().split()
    scores = []
    feedback = []

    for ref, spoken in zip(reference_words, user_words):
        score = phoneme_score(ref, spoken)
        scores.append(score)
        if score == 1.0:
            feedback.append(f"Correct: {spoken}")
        else:
            feedback.append(f"Incorrect: {spoken} (expected: {ref})")

    return scores, feedback

# Function to save audio data and transcribe it
def save_and_transcribe_audio(audio_data):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_data)
        temp_audio_path = temp_audio.name

    transcribed_text = transcribe_audio(temp_audio_path)
    os.remove(temp_audio_path)

    return transcribed_text

# Streamlit App
st.title("Live Pronunciation Assessment App")

# HTML and JavaScript for audio recording
st.markdown("""
    <script>
        let recorder;
        let audioChunks = [];

        async function startRecording() {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recorder = new MediaRecorder(stream);
            recorder.start();

            recorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            recorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks);
                const reader = new FileReader();
                reader.onloadend = function() {
                    const base64data = reader.result.split(',')[1];
                    // Send audio data to Streamlit
                    const xhr = new XMLHttpRequest();
                    xhr.open("POST", "/upload", true);
                    xhr.setRequestHeader("Content-Type", "application/json");
                    xhr.send(JSON.stringify({ audio: base64data }));
                };
                reader.readAsDataURL(audioBlob);
            };
        }

        function stopRecording() {
            recorder.stop();
            audioChunks = [];
        }
    </script>
    <button onclick="startRecording()">Start Recording</button>
    <button onclick="stopRecording()">Stop Recording</button>
""", unsafe_allow_html=True)

# Placeholder for audio upload
audio_buffer = st.file_uploader("Upload a wav file:", type=["wav"], key="uploader")

# Reference sentence input
reference_sentence = st.text_input("Enter the reference sentence you want to pronounce:", "This is India")

# Create a callback for receiving the audio data
if st.session_state.get("audio_data"):
    audio_data = base64.b64decode(st.session_state["audio_data"])
    transcribed_text = save_and_transcribe_audio(audio_data)
    
    if transcribed_text:
        st.write(f"Transcribed Text: {transcribed_text}")

        # Evaluate pronunciation
        scores, feedback = evaluate_pronunciation(reference_sentence, transcribed_text)
        for fb in feedback:
            st.write(fb)

        overall_score = sum(scores) / len(scores) if scores else 0
        st.write(f"Overall Pronunciation Score: {overall_score * 100:.2f}%")
    else:
        st.error("Could not transcribe the audio. Please try again.")

# Callback to handle audio data submission
def handle_audio_upload():
    if st.session_state["audio_data"]:
        st.session_state["audio_data"] = st.session_state["audio_data"]

# Initialize session state for audio data
if "audio_data" not in st.session_state:
    st.session_state["audio_data"] = None

# Main logic for audio upload
if st.button("Evaluate Pronunciation"):
    handle_audio_upload()
