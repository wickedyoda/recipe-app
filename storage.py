import json
import os
import uuid
from pathlib import Path
from datetime import datetime

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/recipe-uploads"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def save_upload(upload_file) -> str:
    suffix = Path(upload_file.filename).suffix if upload_file.filename else ""
    name = f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}{suffix}"
    dest = STORAGE_DIR / name
    with dest.open("wb") as f:
        f.write(upload_file.file.read())
    return str(dest)

def index_recipe(recipe):
    # placeholder: later add embedding generation / vector index update
    return True
