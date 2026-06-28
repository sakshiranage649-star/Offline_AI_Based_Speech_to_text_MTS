import traceback
from backend.models_handler import translator

print("Loading...")
translator.load_model()
print("Loaded. Translating...")
try:
    result = translator.translate("hello", "en", "mr")
    print(result)
except Exception as e:
    traceback.print_exc()
