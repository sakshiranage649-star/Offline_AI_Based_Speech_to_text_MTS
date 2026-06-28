import os
# Strict offline flags are removed so that the app can dynamically download the model 
# if it is missing from the local cache. Once downloaded, it will operate offline automatically.

import threading
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

# Map standard 2-letter codes to NLLB BCP-47 codes
NLLB_LANG_MAP = {
    "en": "eng_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "ru": "rus_Cyrl",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ar": "arb_Arab",
    "hi": "hin_Deva",
    "mr": "mar_Deva",
    "bn": "ben_Beng",
    "te": "tel_Telu",
    "ta": "tam_Taml",
    "gu": "guj_Gujr",
    "ur": "urd_Arab",
    "kn": "kan_Knda",
    "or": "ory_Orya",
    "ml": "mal_Mlym",
    "pa": "pan_Guru"
}

class TranslationModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Upgraded to NLLB-200 for 2x speed and much higher accuracy on non-Latin scripts
        self.model_name = "facebook/nllb-200-distilled-600M"
        self.model = None
        self.tokenizer = None
        self.loaded = False
        self.loading = False

    def start_loading(self):
        if self.loaded or self.loading:
            return
        self.loading = True
        threading.Thread(target=self._load_model_thread, daemon=True).start()

    def _load_model_thread(self):
        print(f"Loading NLLB model {self.model_name} in background...")
        try:
            torch.set_num_threads(4)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            if self.device == "cuda":
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device).half()
            else:
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
                
            self.loaded = True
            print("Translation model loaded successfully.")
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            self.loaded = False
        finally:
            self.loading = False

    def load_model(self):
        if not self.loaded:
            if not self.loading:
                self.start_loading()
            import time
            while self.loading:
                time.sleep(0.1)
        return self.loaded

    def translate(self, text, source_lang, target_lang, fast=False):
        if not self.loaded:
            if self.loading:
                import time
                for _ in range(50):
                    if self.loaded:
                        break
                    time.sleep(0.1)
                if not self.loaded:
                    return "Error: The translation model is still loading in the background. Please wait a few seconds and try again."
            elif not self.load_model():
                return "Error: Translation model could not be loaded."
            
        text = text.strip() if text else ""
        if not text:
            return ""

        CHUNK_LIMIT = 600
        if len(text) > CHUNK_LIMIT:
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if len(paragraphs) <= 1:
                paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            
            if len(paragraphs) <= 1:
                import re
                paragraphs = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

            if not paragraphs:
                paragraphs = [text[i:i+CHUNK_LIMIT] for i in range(0, len(text), CHUNK_LIMIT)]

            chunks = []
            current_chunk = ""
            for p in paragraphs:
                if len(p) > CHUNK_LIMIT:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                    for i in range(0, len(p), CHUNK_LIMIT):
                        chunks.append(p[i:i+CHUNK_LIMIT].strip())
                    continue

                if len(current_chunk) + len(p) + 2 < CHUNK_LIMIT:
                    current_chunk += (p + "\n\n")
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = p + "\n\n"
            if current_chunk:
                chunks.append(current_chunk.strip())

            translated_chunks = []
            batch_size = 4
            for i in range(0, len(chunks), batch_size):
                batch = [c for c in chunks[i:i+batch_size] if c]
                if batch:
                    translated_batch = self._translate_and_verify_batch(batch, source_lang, target_lang, fast=fast)
                    translated_chunks.extend(translated_batch)
            
            return "\n\n".join(translated_chunks)
        else:
            return self._translate_and_verify_batch([text], source_lang, target_lang, fast=fast)[0]

    def _grammar_cleanup(self, text):
        import re
        if not text: return ""
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            text = text[0].upper() + text[1:]
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        return text

    def _translate_and_verify_batch(self, texts, source_lang, target_lang, fast=False):
        import difflib
        if fast:
            translated_batch = self._translate_batch(texts, source_lang, target_lang, num_beams=1)
            return [self._grammar_cleanup(t) for t in translated_batch]
            
        # Lowered num_beams to 2 for much faster generation with NLLB while maintaining grammar accuracy
        translated_batch = self._translate_batch(texts, source_lang, target_lang, num_beams=2)
        
        final_batch = []
        for trans in translated_batch:
            final_batch.append(self._grammar_cleanup(trans))
        return final_batch

    def _translate_batch(self, texts, source_lang, target_lang, num_beams=2):
        try:
            nllb_source = NLLB_LANG_MAP.get(source_lang, "eng_Latn")
            nllb_target = NLLB_LANG_MAP.get(target_lang, "eng_Latn")
            
            self.tokenizer.src_lang = nllb_source
            encoded = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
            
            input_length = encoded.input_ids.shape[1]
            max_new_tokens = min(int(input_length * 1.5) + 20, 512)
            
            with torch.inference_mode():
                generated_tokens = self.model.generate(
                    **encoded, 
                    forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(nllb_target),
                    max_new_tokens=max_new_tokens,
                    num_beams=num_beams,
                )
            translated = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            return translated
            
        except Exception as e:
            print(f"Translation Error: {e}")
            return [f"Error translating text. Unsupported pair or invalid input."] * len(texts)

# Singleton instance
translator = TranslationModel()
