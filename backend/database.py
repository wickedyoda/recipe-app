import logging
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
    entry_cols = {c["name"] for c in insp.get_columns("meal_plan_entries")}
    if "position" not in entry_cols:
        conn.execute(text("ALTER TABLE meal_plan_entries ADD COLUMN position INTEGER NOT NULL DEFAULT 0"))
    # Add is_readonly column to users table
    users_cols = {c["name"] for c in insp.get_columns("users")}
    if "is_readonly" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_readonly INTEGER NOT NULL DEFAULT 0"))
    if "first_name" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(255)"))
    if "last_name" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(255)"))
    if "username" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255)"))
    # Add source_filename column to recipes table
    recipe_cols = {c["name"] for c in insp.get_columns("recipes")}
    if "source_filename" not in recipe_cols:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN source_filename VARCHAR(255)"))
    # Add share_token column to recipes table (for public sharing)
    if "share_token" not in recipe_cols:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN share_token VARCHAR(255)"))
    # Add household_id column to recipes table (for household sharing)
    if "household_id" not in recipe_cols:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN household_id INTEGER"))
    # Create recipe_media table if it doesn't exist
    if "recipe_media" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE recipe_media (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, owner_id INTEGER NOT NULL, file_path VARCHAR(1024) NOT NULL, thumbnail_path VARCHAR(1024), original_filename VARCHAR(255) NOT NULL, media_type VARCHAR(20) NOT NULL, file_size INTEGER, extracted_text TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (owner_id) REFERENCES users(id))"))
    if "recipe_ratings" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE recipe_ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, user_id INTEGER NOT NULL, score INTEGER NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (user_id) REFERENCES users(id), UNIQUE(recipe_id, user_id))"))
    # Create households table
    if "households" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE households (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) NOT NULL, avatar_url VARCHAR(1024), owner_id INTEGER NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (owner_id) REFERENCES users(id))"))
    # Create household_members association table
    if "household_members" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE household_members (id INTEGER PRIMARY KEY AUTOINCREMENT, household_id INTEGER NOT NULL, user_id INTEGER NOT NULL, role VARCHAR(50) NOT NULL DEFAULT 'member', FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE, FOREIGN KEY (user_id) REFERENCES users(id), UNIQUE(household_id, user_id))"))
    # Create household_recipes association table
    if "household_recipes" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE household_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, household_id INTEGER NOT NULL, recipe_id INTEGER NOT NULL, FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE, FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, UNIQUE(household_id, recipe_id))"))
    try:
        _ensure_indexes(conn, insp)
    except Exception as exc:
        logging.getLogger(__name__).warning("index migration skipped: %s", exc)


def _ensure_indexes(conn, insp):
    """Create indexes on frequently queried columns if they don't exist."""
    idx_map = {
        "idx_recipes_owner": ("recipes", "owner_id"),
        "idx_recipes_cookbook": ("recipes", "cookbook_id"),
        "idx_recipe_tags_recipe": ("recipe_tags", "recipe_id"),
        "idx_recipe_tags_tag": ("recipe_tags", "tag_id"),
        "idx_recipe_photos_recipe": ("recipe_photos", "recipe_id"),
        "idx_recipe_photos_owner": ("recipe_photos", "owner_id"),
        "idx_recipe_step_photos_recipe": ("recipe_step_photos", "recipe_id"),
        "idx_notes_recipe": ("notes", "recipe_id"),
        "idx_meal_plans_owner": ("meal_plans", "owner_id"),
        "idx_entries_plan": ("meal_plan_entries", "meal_plan_id"),
        "idx_entries_recipe": ("meal_plan_entries", "recipe_id"),
        "idx_grocery_lists_owner": ("grocery_lists", "owner_id"),
        "idx_grocery_lists_share_token": ("grocery_lists", "share_token"),
        "idx_grocery_items_list": ("grocery_items", "list_id"),
        "idx_grocery_items_recipe": ("grocery_items", "recipe_id"),
        "idx_tags_owner": ("tags", "owner_id"),
        "idx_cookbooks_owner": ("cookbooks", "owner_id"),
        "idx_recipes_share_token": ("recipes", "share_token"),
        "idx_recipe_media_recipe": ("recipe_media", "recipe_id"),
        "idx_recipe_media_owner": ("recipe_media", "owner_id"),
        "idx_ratings_recipe": ("recipe_ratings", "recipe_id"),
        "idx_ratings_user": ("recipe_ratings", "user_id"),
        "idx_household_members_user": ("household_members", "user_id"),
        "idx_household_members_household": ("household_members", "household_id"),
        "idx_household_recipes_household": ("household_recipes", "household_id"),
        "idx_household_recipes_recipe": ("household_recipes", "recipe_id"),
        "idx_recipes_household": ("recipes", "household_id"),
        "idx_users_email": ("users", "email"),
        "idx_users_username": ("users", "username"),
    }
    existing = set()
    try:
        for t in insp.get_indexes("recipes") + insp.get_indexes("meal_plans") + insp.get_indexes("meal_plan_entries"):
            existing.add(t["name"])
        for t in insp.get_indexes("recipe_tags") + insp.get_indexes("recipe_photos") + insp.get_indexes("notes"):
            existing.add(t["name"])
        for t in insp.get_indexes("grocery_lists") + insp.get_indexes("grocery_items") + insp.get_indexes("tags"):
            existing.add(t["name"])
        try:
            for t in insp.get_indexes("cookbooks") + insp.get_indexes("recipe_step_photos"):
                existing.add(t["name"])
        except Exception as exc:
            logging.getLogger(__name__).warning("SQLite index check failed: %s", exc)
        for t in insp.get_indexes("recipe_media"):
            existing.add(t["name"])
        for t in insp.get_indexes("users"):
            existing.add(t["name"])
    except Exception as exc:
        logging.getLogger(__name__).warning("index migration skipped: %s", exc)
    for idx_name, (table, col) in idx_map.items():
        if idx_name not in existing and table in insp.get_table_names():
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({col})"))

def _migrate_mysql(conn):
    insp = inspect(engine)
    users_cols = {c["name"] for c in insp.get_columns("users")}
    if "must_change_password" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0 AFTER is_approved"))
    if "password_changed_at" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN password_changed_at DATETIME NULL AFTER must_change_password"))
    if "is_readonly" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_readonly TINYINT(1) NOT NULL DEFAULT 0 AFTER password_changed_at"))
    if "first_name" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(255) NULL AFTER is_readonly"))
    if "last_name" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(255) NULL AFTER first_name"))
    if "username" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255) NULL AFTER last_name"))
    if "password_history" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE password_history (id INTEGER PRIMARY KEY AUTO_INCREMENT, user_id INTEGER NOT NULL, hashed_password VARCHAR(255) NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))"))
    if "password_reset_tokens" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE password_reset_tokens (id INTEGER PRIMARY KEY AUTO_INCREMENT, user_id INTEGER NOT NULL, token VARCHAR(255) NOT NULL UNIQUE, expires_at DATETIME NOT NULL, used TINYINT(1) DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))"))
    if "position" not in {c["name"] for c in insp.get_columns("meal_plan_entries")}:
        conn.execute(text("ALTER TABLE meal_plan_entries ADD COLUMN position INTEGER NOT NULL DEFAULT 0"))
    # Add source_filename column to recipes table
    recipe_cols = {c["name"] for c in insp.get_columns("recipes")}
    if "source_filename" not in recipe_cols:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN source_filename VARCHAR(255)"))
    # Add share_token column to recipes table (MySQL)
    if "share_token" not in recipe_cols:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN share_token VARCHAR(255)"))
    if "household_id" not in recipe_cols:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN household_id INTEGER NULL"))
    # Create recipe_media table if it doesn't exist (MySQL)
    if "recipe_media" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE recipe_media (id INTEGER PRIMARY KEY AUTO_INCREMENT, recipe_id INTEGER NOT NULL, owner_id INTEGER NOT NULL, file_path VARCHAR(1024) NOT NULL, thumbnail_path VARCHAR(1024), original_filename VARCHAR(255) NOT NULL, media_type VARCHAR(20) NOT NULL, file_size INTEGER, extracted_text TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (owner_id) REFERENCES users(id))"))
    # Create recipe_ratings table if it doesn't exist (MySQL)
    if "recipe_ratings" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE recipe_ratings (id INTEGER PRIMARY KEY AUTO_INCREMENT, recipe_id INTEGER NOT NULL, user_id INTEGER NOT NULL, score INTEGER NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (user_id) REFERENCES users(id), UNIQUE(recipe_id, user_id))"))
    # Create households table if it doesn't exist (MySQL)
    if "households" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE households (id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL, avatar_url VARCHAR(1024), owner_id INTEGER NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (owner_id) REFERENCES users(id))"))
    if "household_members" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE household_members (id INTEGER PRIMARY KEY AUTO_INCREMENT, household_id INTEGER NOT NULL, user_id INTEGER NOT NULL, role VARCHAR(50) NOT NULL DEFAULT 'member', FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE, FOREIGN KEY (user_id) REFERENCES users(id), UNIQUE(household_id, user_id))"))
    if "household_recipes" not in insp.get_table_names():
        conn.execute(text("CREATE TABLE household_recipes (id INTEGER PRIMARY KEY AUTO_INCREMENT, household_id INTEGER NOT NULL, recipe_id INTEGER NOT NULL, FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE, FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, UNIQUE(household_id, recipe_id))"))
    try:
        _ensure_indexes(conn, insp)
    except Exception as exc:
        logging.getLogger(__name__).warning("index migration skipped: %s", exc)