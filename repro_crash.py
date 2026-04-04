import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models_handler import translator
from database import db_handler

def test():
    print("Testing translation...")
    text = "Hello"
    source = "en"
    target = "es"
    
    translated = translator.translate(text, source, target)
    print(f"Translated: {translated}")
    
    print("Testing DB save...")
    db_handler.save_translation(source, target, text, translated)
    print("DB save successful.")

    print("Testing DB fetch...")
    history = db_handler.get_history(1)
    print(f"History: {history}")

if __name__ == "__main__":
    try:
        test()
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()
