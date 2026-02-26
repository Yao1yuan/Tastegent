# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get the database URL from the environment variable set in Render.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# The engine is the entry point to the database.
engine = create_engine(DATABASE_URL)

# Each instance of the SessionLocal class will be a new database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This is a factory for creating base classes for declarative models.
Base = declarative_base()
