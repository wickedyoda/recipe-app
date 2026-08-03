from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models import User, Recipe, Cookbook, Store
from backend.services.auth import get_current_user, require_role
from backend.services.ingest import download_media, ingest_upload, extract_recipe_from_url, extract_recipe_from_upload

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