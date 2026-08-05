import os
import secrets
import urllib.parse
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Response
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

def _ensure_share_token(gl: GroceryList) -> GroceryList:
    if not gl.share_token:
        gl.share_token = secrets.token_urlsafe(12)
    return gl

def _serialize(gl: GroceryList, items: list[GroceryItem]) -> dict:
    return {
        "id": gl.id,
        "name": gl.name,
        "owner_id": gl.owner_id,
        "share_token": gl.share_token,
        "share_enabled": bool(gl.share_token),
        "created_at": gl.created_at.isoformat() if gl.created_at else None,
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "quantity": i.quantity,
                "checked": bool(i.checked),
                "recipe_id": i.recipe_id,
            }
            for i in items
        ],
    }

def _list_text(name: str, items: list[GroceryItem]) -> str:
    lines = [name or "Grocery list"]
    for i in items:
        lines.append(("- [x] " if i.checked else "- [ ] ") + (i.quantity or "") + " " + i.name)
    return "\n".join(lines)

def _html(name: str, items: list[GroceryItem]) -> str:
    body = "<h2>" + escape(name or "Grocery list") + "</h2><ul>"
    for i in items:
        body += "<li>" + ("<s>" if i.checked else "") + escape(i.quantity or "") + " " + escape(i.name) + ("</s>" if i.checked else "") + "</li>"
    body += "</ul>"
    return body

@router.post("", response_model=GroceryListOut)
def create_list(payload: GroceryListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = GroceryList(name=payload.name, owner_id=current_user.id)
    db.add(gl)
    db.commit()
    db.refresh(gl)
    gl = _ensure_share_token(gl)
    db.add(gl)
    db.commit()
    db.refresh(gl)
    return GroceryListOut.model_validate(gl)

@router.get("", response_model=list[GroceryListOut])
def list_lists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        GroceryListOut.model_validate(_ensure_share_token(gl))
        for gl in db.query(GroceryList).filter(GroceryList.owner_id==current_user.id).order_by(GroceryList.created_at.desc()).all()
    ]

@router.get("/{list_id}", response_model=GroceryListOut)
def get_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    gl = _ensure_share_token(gl)
    db.add(gl)
    db.commit()
    db.refresh(gl)
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

@router.patch("/{list_id}", response_model=GroceryListOut)
def update_list(list_id: int, payload: GroceryListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    gl.name = payload.name
    db.add(gl)
    db.commit()
    db.refresh(gl)
    gl = _ensure_share_token(gl)
    db.add(gl)
    db.commit()
    db.refresh(gl)
    return GroceryListOut.model_validate(gl)

@router.patch("/items/{item_id}", response_model=GroceryItemOut)
def update_item(item_id: int, checked: bool | None = None, name: str | None = None, quantity: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(GroceryItem).filter(GroceryItem.id==item_id, GroceryItem.owner_id==current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if checked is not None:
        item.checked = 1 if checked else 0
    if name is not None:
        item.name = name
    if quantity is not None:
        item.quantity = quantity
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

@router.post("/{list_id}/share")
def share_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    gl = _ensure_share_token(gl)
    db.add(gl)
    db.commit()
    db.refresh(gl)
    items = db.query(GroceryItem).filter(GroceryItem.list_id==list_id).order_by(GroceryItem.id).all()
    public_url = (os.getenv("PUBLIC_URL") or "").rstrip("/")
    link = (public_url + "/grocery-lists/public/" + gl.share_token) if public_url else ("/grocery-lists/public/" + gl.share_token)
    text = _list_text(gl.name, items)
    subject = urllib.parse.quote(gl.name or "Grocery list")
    body = urllib.parse.quote(text)
    sms = "sms:?body=" + body
    mailto = "mailto:?subject=" + subject + "&body=" + body
    html = _html(gl.name, items)
    return {
        "share_token": gl.share_token,
        "link": link,
        "mailto": mailto,
        "text": text,
        "html": html,
        "list_name": gl.name,
    }

@router.get("/public/{share_token}")
def public_list(share_token: str, db: Session = Depends(get_db)):
    gl = db.query(GroceryList).filter(GroceryList.share_token==share_token).first()
    if not gl:
        raise HTTPException(status_code=404, detail="List not found")
    items = db.query(GroceryItem).filter(GroceryItem.list_id==gl.id).order_by(GroceryItem.id).all()
    text = _list_text(gl.name, items)
    return Response(content=text, media_type="text/plain; charset=utf-8")

@router.get("/{list_id}/export")
def export_list(list_id: int, fmt: str = "text", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gl = db.query(GroceryList).filter(GroceryList.id==list_id, GroceryList.owner_id==current_user.id).first()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    items = db.query(GroceryItem).filter(GroceryItem.list_id==list_id).order_by(GroceryItem.id).all()
    if fmt == "html":
        content = _html(gl.name, items)
        media_type = "text/html; charset=utf-8"
        filename = (gl.name or "grocery-list") + ".html"
    else:
        content = _list_text(gl.name, items)
        media_type = "text/plain; charset=utf-8"
        filename = (gl.name or "grocery-list") + ".txt"
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})
