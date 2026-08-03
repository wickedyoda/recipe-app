import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recipes.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_schema():
    if not DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("recipes")}
    needed = {
        "prep_time_minutes": "INTEGER",
        "cook_time_minutes": "INTEGER",
        "servings": "INTEGER",
        "difficulty": "VARCHAR(50)",
    }
    with engine.begin() as conn:
        for name, dtype in needed.items():
            if name not in cols:
                conn.execute(text(f"ALTER TABLE recipes ADD COLUMN {name} {dtype}"))
