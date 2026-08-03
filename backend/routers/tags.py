from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import RecipeTag, Tag, User
from backend.schemas import TagCreate, TagOut
from backend.services.auth import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("", response_model=TagOut)
def create_tag(payload: TagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = Tag(name=payload.name, owner_id=current_user.id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return TagOut.model_validate(tag)

@router.get("", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Tag).filter(Tag.owner_id==current_user.id).order_by(Tag.name).all()

@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id==tag_id, Tag.owner_id==current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.query(RecipeTag).filter(RecipeTag.tag_id==tag.id).delete()
    db.delete(tag)
    db.commit()
    return {"deleted": True}
