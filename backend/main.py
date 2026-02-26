# backend/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import io
import uuid
from pathlib import Path
import logging
from dotenv import load_dotenv
from PIL import Image
from sqlalchemy.orm import Session

# Import database-related components
import models, database

# --- 1. Basic Setup & Path Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

IS_RENDER_ENV = 'RENDER' in os.environ
DATA_DIR = Path("/var/data") if IS_RENDER_ENV else Path(__file__).parent.resolve()
UPLOAD_DIR = DATA_DIR / "uploads"

# FIX: Create the directory immediately, before FastAPI initializes and mounts it.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Uploads directory is configured and verified at: {UPLOAD_DIR}")


# --- 2. FastAPI App Initialization ---
app = FastAPI(title="Tastegent API with PostgreSQL")

# --- 3. Startup Event ---
@app.on_event("startup")
def startup_event():
    logger.info("Application startup...")
    # Directory creation removed from here
    logger.info("Initializing database tables...")
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables are ready.")
    logger.info("Startup complete.")


# --- 4. Middleware & Static Files ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True, methods=["*"], headers=["*"],
)

# This will now succeed because the directory was created in step 1
# We keep check_dir=False as a good practice, but the core issue is now solved.
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, check_dir=False), name="uploads")

# --- 5. Pydantic Models ---
class MenuItemBase(BaseModel):
    name: str; description: str; price: float; tags: List[str]; imageUrl: Optional[str] = None
class MenuItemCreate(MenuItemBase): pass
class MenuItemUpdate(MenuItemBase): pass
class MenuItem(MenuItemBase):
    id: int
    class Config: orm_mode = True
class ImageUrlPayload(BaseModel): imageUrl: str

# --- 6. Dependency for Database Session ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 7. API Endpoints ---
@app.get("/")
def get_root(): return {"message": "API is running with PostgreSQL backend."}

@app.get("/menu", response_model=List[MenuItem])
def get_menu(db: Session = Depends(get_db)):
    return db.query(models.MenuItem).order_by(models.MenuItem.id).all()

@app.post("/admin/menu", response_model=MenuItem, status_code=201)
def create_menu_item(item: MenuItemCreate, db: Session = Depends(get_db)):
    db_item = models.MenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/admin/menu/{item_id}", response_model=MenuItem)
def update_menu_item(item_id: int, item_update: MenuItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Menu item not found")
    for key, value in item_update.model_dump().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/admin/menu/{item_id}/image")
def update_menu_item_image(item_id: int, payload: ImageUrlPayload, db: Session = Depends(get_db)):
    db_item = db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Menu item not found")
    db_item.imageUrl = payload.imageUrl
    db.commit()
    return {"message": "Image updated successfully."}

@app.delete("/admin/menu/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Menu item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Menu item deleted successfully."}

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
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)