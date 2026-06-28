import time
import os
import sys

# Change to backend directory to import modules correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.models_handler import translator
from backend.utils import utils_handler
import subprocess

def create_test_video():
    try:
        if not os.path.exists("test2.wav"):
            print("No audio file found to create video.")
            return None
        video_path = "test_video.mp4"
        print("Creating dummy video from test2.wav...")
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=5", "-i", "test2.wav", "-c:v", "libx264", "-c:a", "aac", "-shortest", video_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return video_path
    except Exception as e:
        print(f"Failed to create dummy video: {e}")
        return None

def main():
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write("--- STARTING TRANSLATION TESTS ---\n")
        
        # 1. Text Translation Tests
        f.write("\nLoading Translation Model...\n")
        t0 = time.time()
        translator.load_model()
        t1 = time.time()
        f.write(f"Model Load Time: {t1 - t0:.2f} seconds\n")
        
        source_text = "The quick brown fox jumps over the lazy dog. This is a very common sentence used for testing."
        languages = {"fr": "French", "es": "Spanish", "de": "German", "hi": "Hindi"}
        
        for lang_code, lang_name in languages.items():
            f.write(f"\nTranslating to {lang_name} ({lang_code})...\n")
            t_start = time.time()
            result = translator.translate(source_text, source_lang="en", target_lang=lang_code)
            t_end = time.time()
            f.write(f"Time Taken: {t_end - t_start:.2f} seconds\n")
            f.write(f"Result: {result}\n")
            
        # 2. Audio & Video Tests
        f.write("\n--- STARTING MEDIA TRANSCRIBE TESTS ---\n")
        f.write("Loading STT Model...\n")
        t0 = time.time()
        utils_handler.start_loading()
        while not utils_handler.model_loaded and not (utils_handler.model_loading == False and utils_handler.stt_model is None):
            time.sleep(0.5)
        t1 = time.time()
        f.write(f"STT Model Load Time: {t1 - t0:.2f} seconds\n")
        
        if os.path.exists("test2.wav"):
            f.write("\nTesting Audio Transcription (test2.wav)...\n")
            t_start = time.time()
            audio_text = utils_handler.transcribe_audio("test2.wav")
            t_end = time.time()
            f.write(f"Time Taken: {t_end - t_start:.2f} seconds\n")
            f.write(f"Audio Transcription Result: {audio_text}\n")
        else:
            f.write("\nAudio file 'test2.wav' not found.\n")
            
        vid_path = create_test_video()
        if vid_path:
            f.write(f"\nTesting Video Transcription ({vid_path})...\n")
            t_start = time.time()
            extracted_audio = utils_handler.extract_audio_from_video(vid_path)
            f.write(f"Extracted audio path: {extracted_audio}\n")
            if not extracted_audio.startswith("Error"):
                video_text = utils_handler.transcribe_audio(extracted_audio)
                t_end = time.time()
                f.write(f"Time Taken: {t_end - t_start:.2f} seconds\n")
                f.write(f"Video Transcription Result: {video_text}\n")
            else:
                f.write("Failed to extract audio from video.\n")

if __name__ == '__main__':
    main()
