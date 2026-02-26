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

# Set SSL certificate path for gRPC
os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = certifi.where()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# --- Environment-aware Path Configuration ---
# Check if running in Render environment
IS_RENDER_ENV = 'RENDER' in os.environ
# Define base data directory based on environment
if IS_RENDER_ENV:
    # On Render, use the mounted persistent disk path
    DATA_DIR = Path("/var/data")
    logger.info(f"Running in Render environment. Data directory set to: {DATA_DIR}")
else:
    # Locally, use a relative path from the script location
    DATA_DIR = Path(".")
    logger.info(f"Running in local environment. Data directory set to: {DATA_DIR}")

# Define specific paths for uploads and menu data
UPLOAD_DIR = DATA_DIR / "uploads"
MENU_FILE_PATH = DATA_DIR / "menu.json"

# --- FastAPI App Initialization ---
app = FastAPI()

# --- Application Startup: Ensure directories and files exist ---
# --- FastAPI App Initialization ---
app = FastAPI()

@app.on_event("startup")
def startup_event():
    logger.info("Application startup: Initializing data directories and files.")
    # Create the base data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    # Create the uploads subdirectory if it doesn't exist
    UPLOAD_DIR.mkdir(exist_ok=True)
    # Create an empty menu.json if it doesn't exist, to prevent load errors
    if not MENU_FILE_PATH.exists():
        logger.warning(f"{MENU_FILE_PATH} not found. Creating an empty menu file.")
        with open(MENU_FILE_PATH, "w") as f:
            json.dump([], f)

# Get allowed origins from environment variable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the persistent UPLOAD_DIR
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- Authentication Endpoint ---
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(fake_users_db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

# --- Pydantic Models for API ---
class ImageUrlPayload(BaseModel):
    imageUrl: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    store_id: Optional[str] = None

# --- Data Loading and Saving Functions ---
def load_menu_data():
    """Reads menu data from the persistent JSON file."""
    try:
        with open(MENU_FILE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning(f"{MENU_FILE_PATH} not found or invalid. Starting with an empty menu.")
        return []

def save_menu_data(data):
    """Saves menu data to the persistent JSON file."""
    try:
        with open(MENU_FILE_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        # In a real app, you might want more sophisticated error handling or rollback.
        raise HTTPException(status_code=500, detail=f"Failed to write to menu file: {e}")

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "Restaurant Agent API is running"}

@app.get("/menu")
async def get_menu():
    """Returns the current menu, always reading from the file for consistency."""
    return load_menu_data()

@app.put("/admin/menu/{item_id}/image", dependencies=[Depends(get_current_active_user)])
async def update_menu_item_image(item_id: int, payload: ImageUrlPayload):
    menu_data = load_menu_data() # Load fresh data before modification
    item_found = False
    for item in menu_data:
        if item["id"] == item_id:
            item["imageUrl"] = payload.imageUrl
            item_found = True
            break
    if not item_found:
        raise HTTPException(status_code=404, detail="Menu item not found")
    save_menu_data(menu_data) # Save changes back to the file
    return {"message": f"Successfully updated image for menu item {item_id}"}


@app.post("/admin/menu", response_model=MenuItem, dependencies=[Depends(get_current_active_user)])
async def create_menu_item(item: MenuItemCreate):
    menu_data = load_menu_data()
    # Determine the next ID safely
    new_id = max((i["id"] for i in menu_data), default=0) + 1
    new_item = MenuItem(id=new_id, **item.model_dump(), imageUrl=None)
    menu_data.append(new_item.model_dump())
    save_menu_data(menu_data)
    return new_item


class MenuItemUpdate(BaseModel):
    name: str
    description: str
    price: float
    tags: List[str]
    imageUrl: Optional[str] = None

@app.put("/admin/menu/{item_id}", response_model=MenuItem, dependencies=[Depends(get_current_active_user)])
async def update_menu_item(item_id: int, item_update: MenuItemUpdate):
    menu_data = load_menu_data()
    item_found = False
    updated_item_model = None
    for i, item in enumerate(menu_data):
        if item["id"] == item_id:
            # Update existing item data with new data
            current_item_data = menu_data[i]
            updated_data = item_update.model_dump()

            # Preserve original imageUrl if not provided in the update
            if updated_data.get("imageUrl") is None:
                updated_data["imageUrl"] = current_item_data.get("imageUrl")

            final_item_data = {**current_item_data, **updated_data}
            updated_item_model = MenuItem(**final_item_data)
            menu_data[i] = updated_item_model.model_dump()
            item_found = True
            break

    if not item_found:
        raise HTTPException(status_code=404, detail="Menu item not found")

    save_menu_data(menu_data)
    return updated_item_model

@app.delete("/admin/menu/{item_id}", dependencies=[Depends(get_current_active_user)])
async def delete_menu_item(item_id: int):
    menu_data = load_menu_data()
    original_length = len(menu_data)
    menu_data = [item for item in menu_data if item["id"] != item_id]

    if len(menu_data) == original_length:
        raise HTTPException(status_code=404, detail="Menu item not found")

    save_menu_data(menu_data)
    return {"message": f"Successfully deleted menu item {item_id}"}






@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        if file.content_type.startswith("image/"):
            try:
                content = await file.read()
                image = Image.open(io.BytesIO(content))
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                compressed_filename = f"{uuid.uuid4()}.jpg"
                compressed_path = UPLOAD_DIR / compressed_filename
                max_size = (1920, 1080)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                image.save(compressed_path, "JPEG", quality=85, optimize=True)
                return {
                    "filename": compressed_filename,
                    "url": f"/uploads/{compressed_filename}",
                    "original_filename": file.filename,
                    "content_type": "image/jpeg"
                }
            except Exception as e:
                logger.error(f"Error compressing image: {e}")
                file.file.seek(0)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
            "original_filename": file.filename,
            "content_type": file.content_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_gemini_response(system_prompt, messages):
    try:
        google_key = os.getenv("GOOGLE_API_KEY")
        if not google_key:
            return None
        genai.configure(api_key=google_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        gemini_history = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["Understood. I am ready to help the customer with the menu."]}
        ]
        for msg in messages[:-1]:
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.content]})
        chat_session = model.start_chat(history=gemini_history)
        last_message = messages[-1].content
        response = chat_session.send_message(last_message)
        return {"role": "assistant", "content": response.text}
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

def _get_anthropic_response(system_prompt, messages):
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            return None
        client = Anthropic(api_key=anthropic_key)
        anthropic_messages = []
        for msg in messages:
            if msg.role in ["user", "assistant"]:
                anthropic_messages.append({"role": msg.role, "content": msg.content})
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=anthropic_messages
        )
        return {"role": "assistant", "content": response.content[0].text}
    except Exception as e:
        logger.error(f"Error calling Anthropic: {e}")
        return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

def _get_openai_response(system_prompt, messages):
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return None
        client = OpenAI(api_key=openai_key)
        openai_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})
        response = client.chat.completions.create(
            model="gpt-4",
            messages=openai_messages
        )
        return {"role": "assistant", "content": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}")
        return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

@app.post("/chat")
async def chat(request: ChatRequest):
    menu_str = json.dumps(menu_data, indent=2)
    system_prompt = f"""You are a helpful restaurant agent.
You are helping a customer with their order.
Here is the menu:
{menu_str}

Answer questions about the menu, recommend dishes, and help the customer decide.
Be polite and concise.
"""

    response = _get_gemini_response(system_prompt, request.messages)
    if response:
        return response

    response = _get_anthropic_response(system_prompt, request.messages)
    if response:
        return response

    response = _get_openai_response(system_prompt, request.messages)
    if response:
        return response

    return {
        "role": "assistant",
        "content": "Configuration missing. Please set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in the backend environment."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
