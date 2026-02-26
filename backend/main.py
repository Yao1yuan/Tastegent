# backend/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 引入 Cloudinary
import cloudinary
import cloudinary.uploader

# Import database-related components
import models, database

# --- 1. Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# 不再需要配置本地 UPLOAD_DIR，因为图片将直接飞向云端！
# Cloudinary 会自动读取环境变量中的 CLOUDINARY_URL 进行鉴权，所以这里不需要额外写配置代码。

# --- 2. FastAPI App Initialization ---
app = FastAPI(title="Tastegent API with PostgreSQL")

# --- 3. Startup Event ---
@app.on_event("startup")
def startup_event():
    logger.info("Application startup...")
    logger.info("Initializing database tables...")
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables are ready.")
    logger.info("Startup complete.")

# --- 4. Middleware ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# 不再需要 app.mount("/uploads", ...) 因为图片已经不在服务器上了！

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

# --- 🔥 重写的 Upload 接口 ---
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed.")
    try:
        # 读取上传的文件内容到内存
        content = await file.read()

        # 将文件直接传给 Cloudinary
        upload_result = cloudinary.uploader.upload(
            content,
            folder="tastegent_menu", # 统一放到 Cloudinary 的这个文件夹下，方便管理
            transformation=[
                # 让 Cloudinary 直接帮我们做缩放和优化，省去本地 PIL 的计算！
                {'width': 1920, 'height': 1080, 'crop': 'limit'},
                {'quality': 'auto', 'fetch_format': 'auto'} # 自动转码为最省流的格式（比如 WebP）
            ]
        )

        # Cloudinary 会返回一个安全的 https 链接
        secure_url = upload_result.get("secure_url")
        logger.info(f"Image successfully uploaded to Cloudinary: {secure_url}")

        # 返回给前端这个云端永久链接
        return {"url": secure_url}

    except Exception as e:
        logger.error(f"Cloudinary image upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)