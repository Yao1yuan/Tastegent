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
DATA_DIR = Path("/var/data") if IS_RENDER_ENV else Path(__file__).parent.resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
MENU_FILE_PATH = DATA_DIR / "menu.json"
logger.info(f"Environment detected: {'Render' if IS_RENDER_ENV else 'Local'}. Data directory set to: {DATA_DIR}")

# --- 3. CRITICAL: Pre-startup Directory Creation ---
# This must happen before FastAPI app initialization and mounting
logger.info("Ensuring data directories exist before app startup...")
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
logger.info("Data directories are ready.")

# --- 4. FastAPI App Initialization ---
app = FastAPI(title="Tastegent API")

# --- 5. Application Startup Event ---
# This runs after the app is initialized but before it starts accepting requests.
# Good for non-critical setup like creating initial files.
@app.on_event("startup")
def on_startup():
    logger.info("Application startup event triggered.")
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
# This mount now safely points to a directory that is guaranteed to exist.
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- 7. Security & Authentication Setup ---
SECRET_KEY = os.getenv("SECRET_KEY", "please_change_this_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 8. Pydantic Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class MenuItem(BaseModel):
    id: int
    name: str
    description: str
    price: float
    tags: List[str]
    imageUrl: Optional[str] = None

class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    tags: List[str]

class ImageUrlPayload(BaseModel):
    imageUrl: str

# --- 9. Data Handling Helpers ---
def load_menu_data() -> List[dict]:
    try:
        with open(MENU_FILE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_menu_data(data: List[dict]):
    with open(MENU_FILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

# --- 10. API Endpoints ---
@app.get("/")
def get_root():
    return {"message": "Restaurant Agent API is running"}

@app.get("/menu", response_model=List[MenuItem])
def get_menu():
    return load_menu_data()

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Simplified auth logic for clarity
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_password")
    if form_data.username == ADMIN_USERNAME and pwd_context.verify(form_data.password, pwd_context.hash(ADMIN_PASSWORD)):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.encode(
            {"sub": form_data.username, "exp": datetime.utcnow() + access_token_expires},
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.post("/upload", status_code=201)
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")

        filename = f"{uuid.uuid4()}.jpg"
        save_path = UPLOAD_DIR / filename

        image.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        image.save(save_path, "JPEG", quality=85, optimize=True)

        return {"url": f"/uploads/{filename}"}
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during file upload.")

@app.put("/admin/menu/{item_id}/image")
def update_menu_item_image(item_id: int, payload: ImageUrlPayload):
    menu = load_menu_data()
    item_found = False
    for item in menu:
        if item['id'] == item_id:
            item['imageUrl'] = payload.imageUrl
            item_found = True
            break
    if not item_found:
        raise HTTPException(status_code=404, detail="Menu item not found")
    save_menu_data(menu)
    return {"message": f"Image for item {item_id} updated successfully."}

# ... other admin endpoints for CRUD on menu items would go here ...

# --- Main Entry ---
if __name__ == "__main__":
    import uvicorn
    # This is for local development only
    uvicorn.run(app, host="0.0.0.0", port=8000)
