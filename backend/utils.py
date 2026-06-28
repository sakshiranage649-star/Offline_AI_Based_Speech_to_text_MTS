import os
import wave
import subprocess
import PyPDF2
import threading
import json

class UtilsHandler:
    def __init__(self):
        self.stt_model = None
        self.model_loaded = False
        self.model_loading = False

    def start_loading(self):
        if self.model_loaded or self.model_loading:
            return
        self.model_loading = True
        threading.Thread(target=self._load_model_thread, daemon=True).start()

    def _load_model_thread(self):
        try:
            try:
                from vosk import Model, SetLogLevel
                SetLogLevel(-1)
                print("Loading Vosk STT model in background...")
                model_path = os.path.join(os.path.dirname(__file__), "vosk_model_dir")
                self.stt_model = Model(model_path)
                print("Vosk model loaded successfully.")
            except Exception as base_err:
                print(f"Failed to load Vosk model ({base_err}).")
            self.model_loaded = True
        except Exception as e:
            print(f"Error loading STT model: {e}")
            self.stt_model = None
            self.model_loaded = False
        finally:
            self.model_loading = False

    @property
    def model(self):
        return self.stt_model

    def get_recognizer(self, sample_rate=16000):
        if not self.model_loaded or not self.stt_model:
            return None
        from vosk import KaldiRecognizer
        rec = KaldiRecognizer(self.stt_model, sample_rate)
        rec.SetWords(False)
        return rec

    def transcribe_audio(self, audio_path):
        if not self.model_loaded:
            if self.model_loading:
                return "Error: STT model is still loading in the background. Please try again in a few seconds."
            return "Error: STT model failed to load."
            
        try:
            temp_wav = audio_path.rsplit(".", 1)[0] + "_temp_16k.wav"
            
            ffmpeg_exe = "ffmpeg"
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                pass
            
            cmd = [
                ffmpeg_exe, "-y",
                "-i", audio_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                temp_wav
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                check=True
            )

            from vosk import KaldiRecognizer
            wf = wave.open(temp_wav, "rb")
            
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                return "Error: Audio file must be WAV format mono PCM."
                
            rec = KaldiRecognizer(self.stt_model, wf.getframerate())
            rec.SetWords(False)
            
            result_text = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    result_text += res.get("text", "") + " "
                    
            final_res = json.loads(rec.FinalResult())
            result_text += final_res.get("text", "")
            
            wf.close()
            try:
                os.remove(temp_wav)
            except:
                pass
                
            return result_text.strip()
            
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
            ffmpeg_exe = "ffmpeg"
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                pass
            
            cmd = [
                ffmpeg_exe, "-y",
                "-i", video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                audio_path
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                check=True
            )
            return audio_path
        except Exception as e:
            print(f"Direct ffmpeg audio extraction failed: {e}")
            return f"Error extracting audio: {e}"

utils_handler = UtilsHandler()
