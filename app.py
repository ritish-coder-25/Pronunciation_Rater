import streamlit as st
import speech_recognition as sr
import pronouncing
import wave
import tempfile
import os
import numpy as np
from st_audiorec import st_audiorec

# Function to transcribe audio from file
def transcribe_audio(file_path):
    r = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.error("Could not understand the audio.")
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

st.title("Live Pronunciation Assessment App")

# Record audio from microphone
st.write("Click on the button below to record your pronunciation:")
audio_data = st_audiorec()

reference_sentence = st.text_input("Enter the reference sentence you want to pronounce:", "This is India")

if st.button("Evaluate Pronunciation"):
    if audio_data is not None:
        st.info("Processing your recording...")

        # Create a temporary file to save audio data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            try:
                # Assuming st_audiorec returns raw PCM data, convert to wav format
                audio_bytes = np.array(audio_data, dtype=np.float32)
                # Pydub handles PCM data to convert it to wav format correctly
                audio_segment = AudioSegment(
                    audio_bytes.tobytes(),
                    frame_rate=44100,
                    sample_width=audio_bytes.dtype.itemsize,
                    channels=1
