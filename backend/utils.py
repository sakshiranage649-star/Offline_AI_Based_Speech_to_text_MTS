import os
import wave
import json
import PyPDF2
from moviepy import VideoFileClip
from transformers import pipeline
import librosa
import torch

class UtilsHandler:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            print("Loading Whisper STT model...")
            self.stt_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-tiny", device=0 if self.device=="cuda" else -1)
            print("Whisper model loaded successfully.")
            self.model_loaded = True
        except Exception as e:
            print(f"Error loading Whisper STT model: {e}")
            self.stt_pipeline = None
            self.model_loaded = False

    @property
    def model(self):
        return self.stt_pipeline

    def transcribe_audio(self, audio_path):
        if not self.model_loaded:
            return "Error: STT model failed to load."
            
        try:
            # We use librosa to load the audio file robustly regardless of WAV format constraints
            audio_data, sr = librosa.load(audio_path, sr=16000)
            result = self.stt_pipeline(audio_data)
            return result.get("text", "").strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return f"Error: Transcription failed - {e}"

    def extract_text_from_pdf(self, pdf_path):
        try:
            reader = PyPDF2.PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error extracting PDF: {e}"

    def extract_audio_from_video(self, video_path):
        audio_path = video_path.rsplit(".", 1)[0] + ".wav"
        try:
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec='pcm_s16le', ffmpeg_params=["-ac", "1"])
            video.close()
            return audio_path
        except Exception as e:
            return f"Error extracting audio: {e}"

utils_handler = UtilsHandler()
