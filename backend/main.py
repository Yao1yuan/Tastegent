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

# Import database-related components from our new files
from . import models, database

# --- 1. Basic Setup & Path Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# This is now only for uploads. The database handles menu data persistence.
IS_RENDER_ENV = 'RENDER' in os.environ
DATA_DIR = Path("/var/data") if IS_RENDER_ENV else Path(__file__).parent.resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
logger.info(f"Uploads directory set to: {UPLOAD_DIR}")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- 2. FastAPI App Initialization ---
app = FastAPI(title="Tastegent API with PostgreSQL")

# --- 3. Database Table Creation ---
# This line tells SQLAlchemy to create all the tables defined in our models
# (specifically, the 'menu_items' table) if they don't already exist.
# In a production app, we'd use Alembic for migrations, but this is fine for initial setup.
models.Base.metadata.create_all(bind=database.engine)

# --- 4. Middleware & Static Files ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True, methods=["*"], headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- 5. Pydantic Models (for API validation) ---
class MenuItemBase(BaseModel):
    name: str
    description: str
    price: float
    tags: List[str]
    imageUrl: Optional[str] = None

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpdate(MenuItemBase):
    pass

class MenuItem(MenuItemBase):
    id: int
    class Config:
        orm_mode = True # This allows the model to read data from ORM objects

class ImageUrlPayload(BaseModel):
    imageUrl: str

# --- 6. Dependency for Database Session ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 7. API Endpoints (rewritten for Database) ---
@app.get("/")
def get_root():
    return {"message": "API is running with PostgreSQL backend."}

@app.get("/menu", response_model=List[MenuItem])
def get_menu(db: Session = Depends(get_db)):
    """Returns all menu items from the database."""
    menu_items = db.query(models.MenuItem).order_by(models.MenuItem.id).all()
    return menu_items

@app.post("/admin/menu", response_model=MenuItem, status_code=201)
def create_menu_item(item: MenuItemCreate, db: Session = Depends(get_db)):
    """Creates a new menu item in the database."""
    db_item = models.MenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/admin/menu/{item_id}", response_model=MenuItem)
def update_menu_item(item_id: int, item_update: MenuItemUpdate, db: Session = Depends(get_db)):
    """Updates a menu item in the database."""
    db_item = db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    for key, value in item_update.model_dump().items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/admin/menu/{item_id}/image")
def update_menu_item_image(item_id: int, payload: ImageUrlPayload, db: Session = Depends(get_db)):
    """Updates only the image URL for a menu item."""
    db_item = db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db_item.imageUrl = payload.imageUrl
    db.commit()
    return {"message": f"Image for item {item_id} updated successfully."}


@app.delete("/admin/menu/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    """Deletes a menu item from the database."""
    db_item = db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(db_item)
    db.commit()
    return {"message": f"Menu item {item_id} deleted successfully."}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Uploads an image to the persistent disk."""
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

# ... (You can add back the Auth and AI chat endpoints here if needed, adapting them to the new structure) ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
