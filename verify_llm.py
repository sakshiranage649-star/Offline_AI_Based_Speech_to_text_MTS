import os
import torch

def verify_models():
    print("Dependencies Check:")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    print("-" * 40)
    
    try:
        from transformers import pipeline, M2M100ForConditionalGeneration, M2M100Tokenizer
        
        print("\nVerifying Speech-to-Text Model (openai/whisper-base)...")
        # This will download the model to huggingface cache if it isn't there already
        stt_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-base")
        print("[OK] Whisper base model is installed and cached properly.")
        
        print("\nVerifying Fallback Speech-to-Text Model (openai/whisper-tiny)...")
        stt_pipeline_tiny = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
        print("[OK] Whisper tiny fallback model is installed and cached properly.")
        
        print("\nVerifying Translation Model (facebook/nllb-200-distilled-600M)...")
        # This will download the model to huggingface cache if it isn't there already
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
        model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")
        print("[OK] Translation model is installed and cached properly.")
        
        print("\n" + "=" * 40)
        print("ALL LLM ENGINES ARE FULLY INSTALLED AND READY TO USE.")
        print("=" * 40)

    except ImportError as e:
        print(f"Import Error: {e}. Are transformers and PyTorch installed?")
    except Exception as e:
        print(f"An error occurred while loading the models: {e}")

if __name__ == "__main__":
    verify_models()
