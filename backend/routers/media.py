import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Recipe, User
from backend.services.auth import get_current_user
from backend.services.ingest import (
    download_media,
    extract_recipe_from_upload,
    extract_recipe_from_url,
    ingest_upload,
)

router = APIRouter(prefix="/media", tags=["media"])

class IngestRequest(BaseModel):
    url: str

@router.post("/ingest")
def ingest_media(payload: IngestRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = download_media(payload.url, current_user.id)
    except Exception:
        raise HTTPException(status_code=502, detail="Media download failed")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "ingest failed"))
    return result

@router.post("/upload")
def upload_media(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = ingest_upload(file, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error","upload failed"))
    return result

@router.post("/avatar")
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    suffix = Path(file.filename or "avatar.png").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Avatar must be PNG, JPG, or WebP")
    raw = file.file.read()
    pil_img = Image.open(io.BytesIO(raw))
    pil_img = pil_img.convert("RGBA")
    pil_img.thumbnail((125, 125), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (125, 125), (0, 0, 0, 0))
    offset = ((125 - pil_img.width) // 2, (125 - pil_img.height) // 2)
    canvas.paste(pil_img, offset)
    workdir = Path("backend/media/avatars")
    workdir.mkdir(parents=True, exist_ok=True)
    dest = workdir / f"user_{current_user.id}.png"
    canvas.save(dest, "PNG")
    rel_path = f"media/avatars/user_{current_user.id}.png"
    current_user.avatar_url = f"/media/static/{rel_path}"
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    from backend.schemas import UserOut
    return UserOut.model_validate(current_user)

@router.post("/recipe")
def extract_recipe(payload: IngestRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = extract_recipe_from_url(payload.url, current_user.id)
    except Exception:
        raise HTTPException(status_code=502, detail="Media download failed")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "recipe extraction failed"))
    return result

@router.post("/recipe/upload")
def extract_recipe_from_uploaded_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = extract_recipe_from_upload(file, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail="upload recipe extraction failed")
    return result

@router.get("/items", response_model=list[dict])
def list_media(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Recipe).filter(
        Recipe.owner_id == current_user.id,
        Recipe.source_url.is_not(None) | Recipe.source_path.is_not(None),
    ).order_by(Recipe.created_at.desc()).limit(200).all()
    out = []
    for r in items:
        out.append({
            "id": r.id,
            "title": r.title,
            "source_url": r.source_url,
            "source_path": r.source_path,
            "description": r.description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return out
