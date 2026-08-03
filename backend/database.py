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
    with engine.begin() as conn:
        if DATABASE_URL.startswith("sqlite"):
            _migrate_sqlite(conn)
        elif DATABASE_URL.startswith("mysql"):
            _migrate_mysql(conn)

def _migrate_sqlite(conn):
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("recipes")}
    needed = {
        "prep_time_minutes": "INTEGER",
        "cook_time_minutes": "INTEGER",
        "servings": "INTEGER",
        "difficulty": "VARCHAR(50)",
        "category": "VARCHAR(100)",
        "subcategory": "VARCHAR(100)",
        "flavor_rating": "FLOAT",
        "effort_rating": "FLOAT",
    }
    for name, dtype in needed.items():
        if name not in cols:
            conn.execute(text(f"ALTER TABLE recipes ADD COLUMN {name} {dtype}"))
    _recipe_photos_cols = {c["name"] for c in insp.get_columns("recipe_photos")}
    if "recipe_photos" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE recipe_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, owner_id INTEGER NOT NULL, path VARCHAR(1024) NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (recipe_id) REFERENCES recipes(id), FOREIGN KEY (owner_id) REFERENCES users(id))"))
    grocery_cols = {c["name"] for c in insp.get_columns("grocery_lists")}
    if "share_token" not in grocery_cols:
        conn.execute(text("ALTER TABLE grocery_lists ADD COLUMN share_token VARCHAR(255)"))
    if "recipe_step_photos" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE recipe_step_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, owner_id INTEGER NOT NULL, step_index INTEGER NOT NULL, path VARCHAR(1024) NOT NULL, caption VARCHAR(255), created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (recipe_id) REFERENCES recipes(id), FOREIGN KEY (owner_id) REFERENCES users(id))"))

def _migrate_mysql(conn):
    insp = inspect(engine)
    users_cols = {c["name"] for c in insp.get_columns("users")}
    if "must_change_password" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0 AFTER is_approved"))
    if "password_changed_at" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN password_changed_at DATETIME NULL AFTER must_change_password"))
