import time
import os
import sys
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

def test_quantization():
    print("Loading tokenizer and model...")
    tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_1.2B")
    
    t0 = time.time()
    model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_1.2B")
    t1 = time.time()
    print(f"Standard Load Time: {t1-t0:.2f}s")
    
    print("Quantizing...")
    t2 = time.time()
    model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    t3 = time.time()
    print(f"Quantization Time: {t3-t2:.2f}s")
    
    text = "The quick brown fox jumps over the lazy dog. This is a very common sentence used for testing."
    
    tokenizer.src_lang = "en"
    encoded = tokenizer(text, return_tensors="pt")
    
    # Run once to warmup
    print("Warming up...")
    with torch.inference_mode():
        model.generate(**encoded, forced_bos_token_id=tokenizer.get_lang_id("fr"), max_new_tokens=50, num_beams=2)
        
    print("Benchmarking...")
    t4 = time.time()
    with torch.inference_mode():
        gen = model.generate(**encoded, forced_bos_token_id=tokenizer.get_lang_id("fr"), max_new_tokens=50, num_beams=2)
    t5 = time.time()
    
    result = tokenizer.decode(gen[0], skip_special_tokens=True)
    print(f"Time Taken (beams=2, int8): {t5-t4:.2f}s")
    print(f"Result: {result}")
    
    t6 = time.time()
    with torch.inference_mode():
        gen2 = model.generate(**encoded, forced_bos_token_id=tokenizer.get_lang_id("hi"), max_new_tokens=50, num_beams=2)
    t7 = time.time()
    
    # Try nllb if we can? Just int8 m2m100 first
    print(f"Hindi Time: {t7-t6:.2f}s")
    print(f"Hindi Result: {tokenizer.decode(gen2[0], skip_special_tokens=True)}")

if __name__ == '__main__':
    test_quantization()
