from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import shutil
import google.generativeai as genai
import io
from PIL import Image
import uuid
from pathlib import Path
import logging
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import certifi

# --- 1. Basic Setup ---
os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = certifi.where()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# --- 2. FINAL & ROBUST Path Configuration ---
IS_RENDER_ENV = 'RENDER' in os.environ
DATA_DIR = None

if IS_RENDER_ENV:
    render_disk_path = Path("/var/data")
    # Check if the persistent disk is mounted and writable
    if render_disk_path.exists() and os.access(render_disk_path, os.W_OK):
        DATA_DIR = render_disk_path
        logger.info(f"Persistent disk found and writable at {DATA_DIR}.")
    else:
        # Fallback to a temporary directory if the disk is not available
        DATA_DIR = Path("/tmp/tastegent_temp_data")
        logger.warning(f"!!! PERSISTENT DISK NOT FOUND at '{render_disk_path}' !!!")
        logger.warning(f"Falling back to temporary storage at '{DATA_DIR}'.")
        logger.warning("Data will NOT persist across restarts. Check your Render service 'Disks' configuration.")
else:
    # Local development uses a directory relative to the script file
    DATA_DIR = Path(__file__).parent.resolve()
    logger.info(f"Local environment. Data directory set to: {DATA_DIR}")

UPLOAD_DIR = DATA_DIR / "uploads"
MENU_FILE_PATH = DATA_DIR / "menu.json"

# --- 3. Pre-startup Directory Creation ---
logger.info(f"Ensuring data directory '{DATA_DIR}' and uploads subdir '{UPLOAD_DIR}' exist.")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger.info("Directories are ready.")

# --- 4. FastAPI App Initialization ---
app = FastAPI(title="Tastegent API")

# --- 5. Application Startup Event ---
@app.on_event("startup")
def on_startup():
    logger.info("Executing startup tasks.")
    if not MENU_FILE_PATH.exists():
        logger.warning(f"{MENU_FILE_PATH} not found. Creating a new empty menu file.")
        with open(MENU_FILE_PATH, "w") as f:
            json.dump([], f, indent=2)
    logger.info("Startup tasks complete.")

# --- 6. Middleware & Static Files ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True, methods=["*"], headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- 7. Simplified Models and Data Helpers ---
class MenuItem(BaseModel): id: int; name: str; description: str; price: float; tags: List[str]; imageUrl: Optional[str] = None
def load_menu_data() -> List[dict]:
    try:
        with open(MENU_FILE_PATH, "r") as f: return json.load(f)
    except: return []
def save_menu_data(data: List[dict]):
    with open(MENU_FILE_PATH, "w") as f: json.dump(data, f, indent=2)

# --- 8. API Endpoints ---
@app.get("/")
def get_root(): return {"message": "API is running"}

@app.get("/menu", response_model=List[MenuItem])
def get_menu(): return load_menu_data()

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed.")
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
        filename = f"{uuid.uuid4()}.jpg"
        image.thumbnail((1920, 1080))
        image.save(UPLOAD_DIR / filename, "JPEG", quality=85)
        return {"url": f"/uploads/{filename}"}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed.")

# --- The rest of your endpoints would go here (login, update, etc.) ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
