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
st.write("Click on the button to record your pronunciation:")
audio_data = st_audiorec()

reference_sentence = st.text_input("Enter the reference sentence you want to pronounce:", "This is India")

if st.button("Evaluate Pronunciation"):
    if audio_data is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_bytes = np.frombuffer(audio_data, dtype=np.float32)
            wave_obj = wave.open(temp_audio, "wb")
            wave_obj.setnchannels(1)
            wave_obj.setsampwidth(2)
            wave_obj.setframerate(44100)
            wave_obj.writeframes(audio_bytes.tobytes())
            temp_audio_path = temp_audio.name

        transcribed_text = transcribe_audio(temp_audio_path)
        if transcribed_text:
            st.write(f"Transcribed Text: {transcribed_text}")

            # Evaluate pronunciation
            scores, feedback = evaluate_pronunciation(reference_sentence, transcribed_text)
            for fb in feedback:
                st.write(fb)
            
            overall_score = sum(scores) / len(scores) if scores else 0
            st.write(f"Overall Pronunciation Score: {overall_score * 100:.2f}%")

        os.remove(temp_audio_path)
    else:
        st.warning("Please record an audio first.")
