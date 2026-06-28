# Multilingual Translation: Offline Multilingual AI Translation System - Project Documentation

Welcome to **Multilingual Translation**, a high-performance, secure, and 100% offline translation ecosystem. This document provides a comprehensive overview of the project's architecture, technologies, and features, designed for someone with no prior knowledge of the codebase.

---

## 1. Project Overview
**Multilingual Translation** is a web-based application that allows users to translate text, documents (PDF), and multimedia (Audio/Video) between multiple languages without requiring an internet connection. It is designed for privacy-conscious environments where data security is paramount.

### Core Value Proposition:
- **Offline First**: All AI models run locally on the user's machine.
- **Multimodal**: Supports Text, PDF, Audio, and Video files.
- **Admin Control**: Built-in user management, token systems, and reporting.

---

## 2. Technical Stack ("Every Single Thing Used")

### **Frontend (The User Interface)**
- **HTML5 & CSS3**: Structured and styled using modern, responsive design principles.
- **Vanilla JavaScript**: Handles all client-side logic, API calls (Fetch API), and UI updates.
- **Lucide Icons**: Used for premium, modern iconography.
- **Chart.js**: Powering the data visualizations in the Admin Dashboard.

### **Backend (The Engine)**
- **Python 3.x**: The core programming language.
- **FastAPI**: A modern, high-performance web framework used for building the API.
- **Uvicorn**: An ASGI web server implementation for Python.
- **Pydantic**: Used for data validation and settings management.

### **Database (The Storage)**
- **SQLite**: A lightweight, disk-based database. It requires no separate server process and stores everything in the `transly.db` file.
- **SQLAlchemy/sqlite3**: Python libraries used to interact with the database.

### **AI & Machine Learning (The Intelligence)**
- **Transformers (Hugging Face)**:
    - **Translation Model**: `facebook/m2m100_418M` (A multilingual model supporting 100 languages).
    - **Transcription Model**: `openai/whisper-small` (Used for high-accuracy speech-to-text).
- **PyTorch (torch)**: The underlying deep learning framework for running AI models.
- **Librosa**: Used for advanced audio processing and resampling.

### **Utilities & Libraries**
- **MoviePy**: Used for extracting audio tracks from video files (MP4, AVI, etc.).
- **PyPDF2**: A library for extracting text from PDF documents.
- **python-multipart**: Enables the backend to handle file uploads.
- **python-dotenv**: Manages environment variables and configuration.

---

## 3. Project Structure
```text
Transly/
├── backend/                # Server-side logic
│   ├── app.py              # Main API entry point (FastAPI)
│   ├── database.py         # SQLite database operations & migrations
│   ├── models_handler.py   # AI Translation model loader & logic
│   ├── utils.py            # PDF, Audio, and Video processing utilities
│   └── uploads/            # Temporary storage for uploaded files
├── frontend/               # Client-side files (served by FastAPI)
│   ├── index.html          # Main User Dashboard
│   ├── admin.html          # Administrator Management Dashboard
│   ├── login.html          # Authentication page
│   ├── style.css           # Global application styling
│   └── script.js           # Core frontend logic & API interaction
├── transly.db              # The project database (SQLite)
├── requirements.txt        # List of all Python dependencies
├── run.bat                 # One-click startup script for Windows
└── README.md               # Quick-start guide
```

---

## 4. How the Application Works

### **User Authentication**
Users must register and log in. Every user is assigned a **Token Limit** (e.g., 1000 tokens). Every character translated deducts 1 token from their balance.

### **Translation Flow**
1. **Input**: User types text or uploads a file.
2. **Preprocessing**:
    - If it's a **PDF**, `PyPDF2` extracts the text.
    - If it's a **Video**, `MoviePy` extracts the audio.
    - If it's **Audio**, `Whisper` transcribes it into text.
3. **AI Translation**: The extracted text is sent to the `M2M100` model, which translates it into the target language.
4. **Storage**: The result is saved in the SQLite history table.
5. **Output**: The translation is displayed to the user and their token balance is updated.

### **Admin Capabilities**
Admins (Username: `Admin`, Password: `Admin123`) can:
- View global usage statistics (Charts).
- Manage users (Change roles, update token balances).
- Modify system settings (Welcome tokens, etc.).
- Download CSV reports of all translations.

---

## 5. Setup & Installation
1. **Install Python**: Ensure Python 3.8+ is installed.
2. **Run Startup Script**: Double-click `run.bat`.
   - This script automatically installs dependencies from `requirements.txt`.
   - It starts the server and opens your browser to `http://127.0.0.1:8000`.
3. **Manual Start**:
   ```bash
   pip install -r requirements.txt
   cd backend
   python app.py
   ```

---

*This documentation is generated to provide a 360-degree view of Multilingual Translation. For further questions, refer to the code comments in `app.py` and `database.py`.*
