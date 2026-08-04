from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Note, Recipe, User
from backend.schemas import NoteCreate, NoteOut
from backend.services.auth import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("", response_model=NoteOut)
def create_note(payload: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recipe = db.query(Recipe).filter(Recipe.id==payload.recipe_id, Recipe.owner_id==current_user.id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    note = Note(recipe_id=recipe.id, owner_id=current_user.id, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note)

@router.get("", response_model=list[NoteOut])
def list_notes(recipe_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Note).filter(Note.owner_id==current_user.id)
    if recipe_id:
        q = q.filter(Note.recipe_id==recipe_id)
    return q.order_by(Note.created_at.desc()).all()

@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id==note_id, Note.owner_id==current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"deleted": True}

@router.patch("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id==note_id, Note.owner_id==current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.body = payload.body
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note)
