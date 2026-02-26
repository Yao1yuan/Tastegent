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

# --- Basic Setup ---
os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = certifi.where()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# --- Environment-aware Path Configuration ---
IS_RENDER_ENV = 'RENDER' in os.environ
DATA_DIR = Path("/var/data") if IS_RENDER_ENV else Path(".")
UPLOAD_DIR = DATA_DIR / "uploads"
MENU_FILE_PATH = DATA_DIR / "menu.json"
logger.info(f"Data directory set to: {DATA_DIR}")

# --- FastAPI App Initialization (CRITICAL: MUST be defined before use) ---
app = FastAPI()

# --- Application Startup Event (CRITICAL: Must be defined after app is initialized) ---
@app.on_event("startup")
def startup_event():
    logger.info("Initializing data directories and files.")
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    if not MENU_FILE_PATH.exists():
        logger.warning(f"{MENU_FILE_PATH} not found. Creating an empty menu file.")
        with open(MENU_FILE_PATH, "w") as f:
            json.dump([], f)

# --- Middleware and Static Files ---
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- JWT, Password Hashing, and Authentication ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_serect_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    disabled: bool = False

admin_password = os.getenv("ADMIN_PASSWORD", "default_password")
hashed_password = pwd_context.hash(admin_password)
fake_users_db = {
    os.getenv("ADMIN_USERNAME", "admin"): UserInDB(
        username=os.getenv("ADMIN_USERNAME", "admin"),
        hashed_password=hashed_password,
    )
}

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    # ... (Authentication logic remains the same)
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None or user.disabled:
        raise credentials_exception
    return user

# --- Data Models ---
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

# ... (Other models remain the same)

# --- Data Handling Functions ---
def load_menu_data():
    try:
        with open(MENU_FILE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_menu_data(data):
    with open(MENU_FILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

# --- API Endpoints ---
@app.get("/")
def root():
    return {"message": "Restaurant Agent API is running"}

@app.get("/menu", response_model=List[MenuItem])
def get_menu():
    return load_menu_data()

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": user.username, "exp": datetime.utcnow() + access_token_expires}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}

# ... (All other endpoints: create, update, delete, upload, chat logic remain the same but use load/save helpers) ...

@app.put("/admin/menu/{item_id}/image")
def update_menu_item_image(item_id: int, payload: dict, current_user: UserInDB = Depends(get_current_active_user)):
    menu_data = load_menu_data()
    for item in menu_data:
        if item["id"] == item_id:
            item["imageUrl"] = payload.get("imageUrl")
            save_menu_data(menu_data)
            return {"message": "Image updated successfully"}
    raise HTTPException(status_code=404, detail="Menu item not found")

@app.post("/admin/menu", response_model=MenuItem)
def create_menu_item(item: MenuItemCreate, current_user: UserInDB = Depends(get_current_active_user)):
    menu_data = load_menu_data()
    new_id = max((i["id"] for i in menu_data), default=0) + 1
    new_item = MenuItem(id=new_id, **item.model_dump(), imageUrl=None)
    menu_data.append(new_item.model_dump())
    save_menu_data(menu_data)
    return new_item

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")

        content = await file.read()
        image = Image.open(io.BytesIO(content))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        compressed_filename = f"{uuid.uuid4()}.jpg"
        compressed_path = UPLOAD_DIR / compressed_filename

        image.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        image.save(compressed_path, "JPEG", quality=85, optimize=True)

        return {
            "url": f"/uploads/{compressed_filename}"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
