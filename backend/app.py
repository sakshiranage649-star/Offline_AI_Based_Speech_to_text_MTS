from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import os
import shutil
import uuid
from typing import Optional
import json
import asyncio

# Import our handlers
from models_handler import translator
from database import db_handler
from utils import utils_handler

app = FastAPI(title="Multilingual Translation API")

@app.on_event("startup")
async def startup_event():
    # Asynchronously load translation and STT models on startup
    translator.start_loading()
    utils_handler.start_loading()

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

# --- Auth Endpoints ---

@app.post("/register")
async def register(data: dict):
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    phone = data.get("phone")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    success = db_handler.register_user(username, password, email, phone)
    if success:
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login")
async def login(data: dict):
    username = data.get("username")
    password = data.get("password")
    user = db_handler.authenticate_user(username, password)
    if user:
        return {"user": user}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/user-info/{user_id}")
async def get_user_info(user_id: int):
    user = db_handler.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/user-update")
async def update_user(data: dict):
    user_id = data.get("user_id")
    email = data.get("email")
    phone = data.get("phone")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    success = db_handler.update_user(user_id, email, phone)
    if success:
        return {"message": "Profile updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update profile")

# --- Admin Endpoints ---

@app.get("/admin/reports")
async def get_reports(admin_id: Optional[int] = Header(None)):
    # Basic check for admin role
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    admin = db_handler.get_user_by_id(admin_id)
    if not admin or admin['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reports = db_handler.get_admin_reports()
    return reports

@app.get("/admin/settings")
async def get_settings(admin_id: Optional[int] = Header(None)):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    admin = db_handler.get_user_by_id(admin_id)
    if not admin or admin['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = db_handler.get_settings()
    return settings

@app.post("/admin/update-setting")
async def update_setting(data: dict, admin_id: Optional[int] = Header(None)):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    admin = db_handler.get_user_by_id(admin_id)
    if not admin or admin['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    key = data.get("key")
    value = data.get("value")
    if not key or value is None:
        raise HTTPException(status_code=400, detail="Key and value required")
    
    success = db_handler.update_setting(key, value)
    if success:
        return {"message": "Setting updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update setting")

@app.post("/admin/update-user-tokens")
async def update_user_tokens(data: dict, admin_id: Optional[int] = Header(None)):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    admin = db_handler.get_user_by_id(admin_id)
    if not admin or admin['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user_id = data.get("user_id")
    tokens = data.get("tokens")
    if user_id is None or tokens is None:
        raise HTTPException(status_code=400, detail="User ID and tokens required")
    
    success = db_handler.update_user_tokens(user_id, tokens)
    if success:
        return {"message": "Tokens updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update tokens")

# --- Translation Endpoints ---

@app.post("/translate")
async def translate_text(data: dict):
    text = data.get("text")
    source = data.get("source", "en")
    target = data.get("target", "fr")
    user_id = data.get("user_id", 1) # Default to anonymous/system user if not provided
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")
    
    # Check tokens
    user = db_handler.get_user_by_id(user_id)
    if user and user['tokens'] < len(text):
        raise HTTPException(status_code=402, detail="Insufficient tokens")
    
    # Run translation
    translated = translator.translate(text, source, target)
    
    # Save to history and deduct tokens
    db_handler.save_translation(source, target, text, translated, user_id)
    
    return {"translated": translated}

@app.get("/history")
async def get_history(limit: int = 10, q: str = "", user_id: Optional[int] = None):
    history = db_handler.get_history(limit, q, user_id)
    return {"history": history}

@app.post("/upload-translate")
async def upload_and_translate(
    file: UploadFile = File(...), 
    source: str = Form("en"), 
    target: str = Form("fr"),
    user_id: int = Form(1)
):
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
            if audio_path.startswith("Error"):
                error = audio_path
            else:
                extracted_text = utils_handler.transcribe_audio(audio_path)
                try:
                    os.remove(audio_path) # cleanup
                except: pass
                if extracted_text.startswith("Error"):
                    error = extracted_text
        elif ext in ["wav", "mp3", "ogg", "webm", "m4a"]:
            extracted_text = utils_handler.transcribe_audio(file_path)
            if extracted_text.startswith("Error"):
                error = extracted_text
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    extracted_text = f.read()
            except:
                error = "Unsupported file type or extraction failed."

        if extracted_text is not None and not error:
            # Check tokens
            user = db_handler.get_user_by_id(user_id)
            if user and user['tokens'] < len(extracted_text):
                return JSONResponse(status_code=402, content={"detail": "Insufficient tokens"})

            # Translate the text. The translation handler (translator.translate)
            # transparently handles text chunking, dynamic length optimization, 
            # and greedy search to achieve maximum CPU speed.
            translated = translator.translate(extracted_text, source, target)

            db_handler.save_translation(source, target, extracted_text, translated, user_id)
            return {"source_text": extracted_text, "translated": translated}
        else:
            return JSONResponse(status_code=400, content={"detail": error or "Extraction failed."})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Server Error: {e}"})
    finally:
        try:
            os.remove(file_path)
        except: pass

@app.websocket("/ws/realtime-translate")
async def websocket_translate(websocket: WebSocket):
    await websocket.accept()
    
    source_lang = "en"
    target_lang = "fr"
    user_id = 1
    
    # Wait until STT is ready
    while not utils_handler.model_loaded:
        if not utils_handler.model_loading:
            utils_handler.start_loading()
        await websocket.send_json({"type": "status", "message": "Loading STT model..."})
        await asyncio.sleep(1)
        
    # Wait for the first configuration message
    initial_message = await websocket.receive()
    sample_rate = 16000
    if "text" in initial_message:
        try:
            data = json.loads(initial_message["text"])
            if "source" in data:
                source_lang = data["source"]
            if "target" in data:
                target_lang = data["target"]
            if "user_id" in data:
                user_id = data["user_id"]
            if "sample_rate" in data:
                sample_rate = data["sample_rate"]
        except:
            pass

    rec = utils_handler.get_recognizer(sample_rate)
    if not rec:
        await websocket.send_json({"type": "error", "message": "Failed to initialize STT recognizer."})
        await websocket.close()
        return

    await websocket.send_json({"type": "status", "message": "Ready"})

    try:
        while True:
            # We receive either text (metadata) or bytes (audio PCM)
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if "source" in data:
                        source_lang = data["source"]
                    if "target" in data:
                        target_lang = data["target"]
                    if "user_id" in data:
                        user_id = data["user_id"]
                except:
                    pass
            elif "bytes" in message:
                audio_data = message["bytes"]
                if len(audio_data) == 0:
                    continue
                
                if rec.AcceptWaveform(audio_data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "").strip()
                    if text:
                        # If user selected a different source language, translate STT output to that language for display
                        display_text = text
                        if source_lang != "en":
                            display_text = translator.translate(text, "en", source_lang, fast=True)
                            translated = translator.translate(text, "en", target_lang, fast=True)
                        else:
                            translated = translator.translate(text, source_lang, target_lang, fast=True)
                            
                        await websocket.send_json({
                            "type": "result",
                            "source_text": display_text,
                            "translated": translated
                        })
                        # Optionally save history in background
                        db_handler.save_translation(source_lang, target_lang, display_text, translated, user_id)
                else:
                    res = json.loads(rec.PartialResult())
                    partial_text = res.get("partial", "").strip()
                    if partial_text:
                        display_partial = partial_text
                        if source_lang != "en":
                            display_partial = translator.translate(partial_text, "en", source_lang, fast=True)
                        await websocket.send_json({
                            "type": "partial",
                            "source_text": display_partial
                        })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

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
        
    if translator.loaded:
        model_status = "Ready"
    elif translator.loading:
        model_status = "Loading"
    else:
        model_status = "Standby"
        
    if utils_handler.model_loaded:
        stt_status = "Ready"
    elif utils_handler.model_loading:
        stt_status = "Loading"
    else:
        stt_status = "Missing Assets"
    
    return {
        "database": db_status,
        "translation_engine": model_status,
        "transcription_engine": stt_status,
        "device": translator.device,
        "version": "1.0.0"
    }

# Serve frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8080, reload=True)

