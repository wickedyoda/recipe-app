from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models import User, Recipe, Cookbook, Store
from ..services.auth import get_current_user, require_role
from ..services.ingest import download_media

router = APIRouter(prefix="/media", tags=["media"])

class IngestRequest(BaseModel):
    url: str

@router.post("/ingest")
def ingest_media(payload: IngestRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = download_media(payload.url, current_user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error","ingest failed"))
    return result

@router.get("/items")
def list_media(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Recipe).filter(Recipe.owner_id==current_user.id, Recipe.store==Store.local).order_by(Recipe.created_at.desc()).limit(200).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "source_url": r.source_url,
            "source_path": r.source_path,
            "description": r.description,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

@router.get("/cookbooks")
def list_cookbooks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Cookbook).filter(Cookbook.owner_id==current_user.id).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "store": c.store.value,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]

@router.post("/cookbooks")
def create_cookbook(name: str, description: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cb = Cookbook(name=name, description=description, store=Store.local, owner_id=current_user.id)
    db.add(cb)
    db.commit()
    db.refresh(cb)
    return {
        "id": cb.id,
        "name": cb.name,
        "description": cb.description,
        "store": cb.store.value,
        "created_at": cb.created_at.isoformat(),
    }
