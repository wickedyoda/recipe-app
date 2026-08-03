from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
    result = download_media(payload.url, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error","ingest failed"))
    return result

@router.post("/upload")
def upload_media(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = ingest_upload(file, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error","upload failed"))
    return result

@router.post("/recipe")
def extract_recipe(payload: IngestRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = extract_recipe_from_url(payload.url, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error","recipe extraction failed"))
    return result

@router.post("/recipe/upload")
def extract_recipe_from_uploaded_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = extract_recipe_from_upload(file, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error","upload recipe extraction failed"))
    return result

@router.get("/items", response_model=list[dict])
def list_media(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Recipe).filter(
        Recipe.owner_id == current_user.id,
        (Recipe.source_url != None) | (Recipe.source_path != None)
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
