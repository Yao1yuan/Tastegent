# backend/models.py
from sqlalchemy import Column, Integer, String, Float, ARRAY
from .database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    tags = Column(ARRAY(String))
    imageUrl = Column(String, nullable=True)
