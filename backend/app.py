from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import os
import shutil
import uuid

# Import our handlers
from models_handler import translator
from database import db_handler
from utils import utils_handler

app = FastAPI(title="Transly API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder to store uploaded files temporarily
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/translate")
async def translate_text(data: dict):
    text = data.get("text")
    source = data.get("source", "en")
    target = data.get("target", "fr")
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")
    
    # Run translation
    translated = translator.translate(text, source, target)
    
    # Save to history
    db_handler.save_translation(source, target, text, translated)
    
    return {"translated": translated}

@app.get("/history")
async def get_history(limit: int = 10, q: str = ""):
    history = db_handler.get_history(limit, q)
    return {"history": history}

@app.get("/status")
def get_status():
    try:
        if db_handler.connection:
            cursor = db_handler.connection.cursor()
            cursor.execute("SELECT 1")
            db_status = "Connected"
        else:
            db_handler.connect()
            db_status = "Connected" if db_handler.connection else "Disconnected"
    except Exception:
        db_status = "Disconnected"
        
    model_status = "Ready" # Models load dynamically on first request
    stt_status = "Ready" if utils_handler.model else "Missing Assets"
    
    return {
        "database": db_status,
        "translation_engine": model_status,
        "transcription_engine": stt_status,
        "device": translator.device,
        "version": "1.0.0"
    }

@app.post("/upload-translate")
async def upload_and_translate(file: UploadFile = File(...), source: str = Form("en"), target: str = Form("fr")):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file locally
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    extracted_text = ""
    error = None
    
    try:
        # Check file extension
        ext = file.filename.split(".")[-1].lower()
        
        if ext == "pdf":
            extracted_text = utils_handler.extract_text_from_pdf(file_path)
        elif ext in ["mp4", "avi", "mkv", "mov"]:
            audio_path = utils_handler.extract_audio_from_video(file_path)
            extracted_text = utils_handler.transcribe_audio(audio_path)
            try:
                os.remove(audio_path) # cleanup
            except: pass
        elif ext in ["wav", "mp3", "ogg"]:
            # Handle audio upload for STT directly
            # For simplicity, extract audio if it's not wav or not PCM
            # But assume wav for now for direct Vosk use
            extracted_text = utils_handler.transcribe_audio(file_path)
        else:
            # Fallback for text files or unrecognized
            try:
                # Check if it was returned as error string from earlier steps
                if extracted_text.startswith("Error"):
                    error = extracted_text
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        extracted_text = f.read()
            except:
                if not extracted_text:
                    error = "Unsupported file type or extraction failed."

        if extracted_text and not error:
            translated = translator.translate(extracted_text, source, target)
            db_handler.save_translation(source, target, extracted_text, translated)
            return {"source_text": extracted_text, "translated": translated}
        else:
            return JSONResponse(status_code=400, content={"detail": error or "Extraction failed."})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Server Error: {e}"})
    finally:
        # Clean up
        try:
            os.remove(file_path)
        except: pass

# Serve frontend
# Get the absolute path to the frontend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

if not os.path.exists(FRONTEND_DIR):
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
