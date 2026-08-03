from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import GroceryItem, GroceryList, Recipe, User
from backend.schemas import (
    GroceryItemCreate,
    GroceryItemOut,
    GroceryListCreate,
    GroceryListOut,
)
from backend.services.auth import get_current_user

router = APIRouter(prefix="/grocery-lists", tags=["grocery-lists"])

@router.post("", response_model=GroceryListOut)
def create_list(payload: GroceryListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = GroceryList(name=payload.name, owner_id=current_user.id)
    db.add(gl)
    db.commit()
    db.refresh(gl)
    return GroceryListOut.model_validate(gl)

@router.get("", response_model=list[GroceryListOut])
def list_lists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(GroceryList).filter(GroceryList.owner_id==current_user.id).order_by(GroceryList.created_at.desc()).all()

@router.get("/{list_id}", response_model=GroceryListOut)
def get_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return GroceryListOut.model_validate(gl)

@router.post("/{list_id}/items", response_model=GroceryItemOut)
def add_item(list_id: int, payload: GroceryItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    if payload.recipe_id:
        recipe = db.query(Recipe).filter(Recipe.id==payload.recipe_id, Recipe.owner_id==current_user.id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
    item = GroceryItem(list_id=gl.id, recipe_id=payload.recipe_id, name=payload.name, quantity=payload.quantity, owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return GroceryItemOut.model_validate(item)

@router.get("/{list_id}/items", response_model=list[GroceryItemOut])
def list_items(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return db.query(GroceryItem).filter(GroceryItem.list_id==list_id).order_by(GroceryItem.id).all()


@router.patch("/items/{item_id}", response_model=GroceryItemOut)
def update_item(item_id: int, checked: bool | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(GroceryItem).filter(GroceryItem.id==item_id, GroceryItem.owner_id==current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if checked is not None:
        item.checked = 1 if checked else 0
    db.add(item)
    db.commit()
    db.refresh(item)
    return GroceryItemOut.model_validate(item)

@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(GroceryItem).filter(GroceryItem.id==item_id, GroceryItem.owner_id==current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"deleted": True}
