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

# --- 2. Environment-aware Path Configuration ---
IS_RENDER_ENV = 'RENDER' in os.environ
# On Render, /var/data is the mount path for the persistent disk and it already exists.
# Locally, we'll use the current directory.
DATA_DIR = Path("/var/data") if IS_RENDER_ENV else Path(__file__).parent.resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
MENU_FILE_PATH = DATA_DIR / "menu.json"
logger.info(f"Environment: {'Render' if IS_RENDER_ENV else 'Local'}. Data Dir: {DATA_DIR}")

# --- 3. Pre-startup Directory Creation ---
# We do NOT create DATA_DIR itself, as Render provides it.
# We only ensure our required subdirectory exists within it.
logger.info(f"Ensuring upload directory exists at: {UPLOAD_DIR}")
UPLOAD_DIR.mkdir(exist_ok=True)
logger.info("Upload directory is ready.")

# --- 4. FastAPI App Initialization (MUST be defined before it's used) ---
app = FastAPI(title="Tastegent API", docs_url="/api/docs", openapi_url="/api/openapi.json")

# --- 5. Application Startup Event ---
@app.on_event("startup")
def on_startup():
    logger.info("Executing startup tasks.")
    if not MENU_FILE_PATH.exists():
        logger.warning(f"{MENU_FILE_PATH} not found. Creating a new empty menu file.")
        with open(MENU_FILE_PATH, "w") as f:
            json.dump([], f, indent=2)
    logger.info("Startup tasks complete.")

# --- 6. Middleware & Static Files Mounting ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# This now safely points to a directory we know exists.
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- 7. Security & Authentication ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# --- 8. Pydantic Models & Data Helpers ---
class Token(BaseModel): accessToken: str; token_type: str
class MenuItem(BaseModel): id: int; name: str; description: str; price: float; tags: List[str]; imageUrl: Optional[str] = None
class MenuItemCreate(BaseModel): name: str; description: str; price: float; tags: List[str]
class ImageUrlPayload(BaseModel): imageUrl: str

def load_menu_data() -> List[dict]:
    try:
        with open(MENU_FILE_PATH, "r") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def save_menu_data(data: List[dict]):
    with open(MENU_FILE_PATH, "w") as f: json.dump(data, f, indent=2)

# --- 10. API Endpoints ---
@app.get("/")
def get_root(): return {"message": "Restaurant Agent API is running"}

@app.get("/menu", response_model=List[MenuItem])
def get_menu(): return load_menu_data()

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Simplified auth for this context
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_password")
    if form_data.username == ADMIN_USERNAME and pwd_context.verify(form_data.password, pwd_context.hash(ADMIN_PASSWORD)):
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = jwt.encode({"sub": form_data.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
        filename = f"{uuid.uuid4()}.jpg"
        image.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        image.save(UPLOAD_DIR / filename, "JPEG", quality=85, optimize=True)
        return {"url": f"/uploads/{filename}"}
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed.")

@app.put("/admin/menu/{item_id}/image")
def update_item_image(item_id: int, payload: ImageUrlPayload):
    menu = load_menu_data()
    if not any(item['id'] == item_id for item in menu):
        raise HTTPException(status_code=404, detail="Menu item not found")
    for item in menu:
        if item['id'] == item_id:
            item['imageUrl'] = payload.imageUrl
            break
    save_menu_data(menu)
    return {"message": "Image updated successfully."}

# Add other CRUD endpoints here if needed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
