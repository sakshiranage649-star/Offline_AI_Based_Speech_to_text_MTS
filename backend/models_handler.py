import os
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import torch

class TranslationModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        self.model_name = "facebook/m2m100_418M"
        self.model = None
        self.tokenizer = None
        self.loaded = False

    def load_model(self):
        if not self.loaded:
            print(f"Loading multilingual model {self.model_name}...")
            try:
                self.tokenizer = M2M100Tokenizer.from_pretrained(self.model_name)
                self.model = M2M100ForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
                self.loaded = True
                print("Translation model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")
        return self.loaded

    def translate(self, text, source_lang, target_lang):
        if not self.load_model():
            return "Error: Translation model could not be loaded."
            
        # Map our short codes to m2m100 expected codes if needed (m2m100 uses standard 2 letter codes mostly)
        # en, fr, de, es, it, pt, ru, zh, ja, ar, hi
        try:
            self.tokenizer.src_lang = source_lang
            encoded = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # target_lang can be passed to generate
            target_lang_id = self.tokenizer.get_lang_id(target_lang)
            
            generated_tokens = self.model.generate(**encoded, forced_bos_token_id=target_lang_id)
            translated = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            return translated[0]
            
        except Exception as e:
            print(f"Translation Error: {e}")
            return f"Error translating text. Unsupported pair or invalid input."

# Singleton instance
translator = TranslationModel()
