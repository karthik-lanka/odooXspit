import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Add SSL mode for production databases (Render, etc.)
engine_args = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# If using external PostgreSQL (Render), ensure SSL is enabled
if "dpg-" in DATABASE_URL or "render" in DATABASE_URL.lower():
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL + ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"
    engine_args["connect_args"] = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
