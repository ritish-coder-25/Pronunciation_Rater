import streamlit as st
import speech_recognition as sr
import pronouncing
import os
import tempfile
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import av

# Define the audio processor
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio_data = frame.to_ndarray()
        self.audio_frames.append(audio_data)
        return frame

    def get_audio_buffer(self):
        if len(self.audio_frames) == 0:
            return None
        audio_data = np.concatenate(self.audio_frames, axis=1).flatten()
        return audio_data

    def reset_audio_buffer(self):
        self.audio_frames = []

# Function to save the audio data to a file
def save_audio_to_file(audio_data, file_path):
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # Assuming 16-bit audio
        wf.setframerate(16000)  # Assuming 16kHz sample rate
        wf.writeframes(audio_data)

# Transcribe the audio
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

# Calculate phoneme score
def phoneme_score(ref_word, spoken_word):
    ref_phonemes = pronouncing.phones_for_word(ref_word)
    spoken_phonemes = pronouncing.phones_for_word(spoken_word)

    if not ref_phonemes or not spoken_phonemes:
        return 0

    ref_phoneme_list = ref_phonemes[0].split()
    spoken_phoneme_list = spoken_phonemes[0].split()

    matches = sum(1 for ref, spoken in zip(ref_phoneme_list, spoken_phoneme_list) if ref == spoken)
    return matches / max(len(ref_phoneme_list), len(spoken_phoneme_list))

# Evaluate pronunciation
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

reference_sentence = st.text_input("Enter the reference sentence you want to pronounce:", "This is India")

# We use streamlit-webrtc to record audio from the user's microphone
audio_processor = webrtc_streamer(
    key="pronunciation-assessment",
    mode=WebRtcMode.SENDRECV,
    audio_receiver_size=1024,
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

if st.button("Evaluate Pronunciation"):
    if audio_processor:
        audio_buffer = audio_processor.audio_processor.get_audio_buffer()
        if audio_buffer is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                save_audio_to_file(audio_buffer, temp_audio.name)
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
            st.warning("Please record some audio first.")
    else:
        st.warning("Audio processor is not available. Please try again.")

