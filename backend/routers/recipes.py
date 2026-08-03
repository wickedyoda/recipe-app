import json
import os
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Recipe, RecipePhoto, RecipeTag, Store, Tag, User
from backend.schemas import RecipeCreate, RecipeOut
from backend.services.auth import get_current_user

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("", response_model=RecipeOut)
def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recipe = Recipe(
        title=payload.title,
        description=payload.description,
        ingredients=payload.ingredients,
        instructions=payload.instructions,
        source_url=payload.source_url,
        source_path=payload.source_path,
        store=Store[payload.store] if payload.store else Store.local,
        owner_id=current_user.id,
        cookbook_id=payload.cookbook_id,
        rating=payload.rating,
        prep_time_minutes=payload.prep_time_minutes,
        cook_time_minutes=payload.cook_time_minutes,
        servings=payload.servings,
        difficulty=payload.difficulty,
        category=payload.category,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    if payload.tag_ids:
        for tag_id in payload.tag_ids:
            tag = db.query(Tag).filter(Tag.id==tag_id, Tag.owner_id==current_user.id).first()
            if not tag:
                raise HTTPException(status_code=400, detail=f"Tag {tag_id} not found")
            db.add(RecipeTag(recipe_id=recipe.id, tag_id=tag.id))
        db.commit()
        db.refresh(recipe)
    return RecipeOut.model_validate(recipe)

@router.get("", response_model=list[RecipeOut])
def list_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), q: str = ""):
    rows = db.query(Recipe).filter(Recipe.owner_id==current_user.id)
    if q:
        rows = rows.filter(Recipe.title.ilike(f"%{q}%"))
    rows = rows.order_by(Recipe.created_at.desc()).limit(200).all()
    out = []
    for r in rows:
        data = RecipeOut.model_validate(r).model_dump()
        data["tags"] = [t.name for t in db.query(Tag).join(RecipeTag, RecipeTag.tag_id==Tag.id).filter(RecipeTag.recipe_id==r.id).all()]
        data["photos"] = [p.path for p in db.query(RecipePhoto).filter(RecipePhoto.recipe_id==r.id).order_by(RecipePhoto.id.asc()).all()]
        out.append(data)
    return out

@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    data = RecipeOut.model_validate(r).model_dump()
    data["tags"] = [t.name for t in db.query(Tag).join(RecipeTag, RecipeTag.tag_id==Tag.id).filter(RecipeTag.recipe_id==r.id).all()]
    data["photos"] = [p.path for p in db.query(RecipePhoto).filter(RecipePhoto.recipe_id==r.id).order_by(RecipePhoto.id.asc()).all()]
    return data

@router.patch("/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, payload: RecipeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    r.title = payload.title
    r.description = payload.description
    r.ingredients = payload.ingredients
    r.instructions = payload.instructions
    r.source_url = payload.source_url
    r.source_path = payload.source_path
    if payload.store:
        r.store = Store[payload.store]
    r.cookbook_id = payload.cookbook_id
    r.rating = payload.rating
    r.prep_time_minutes = payload.prep_time_minutes
    r.cook_time_minutes = payload.cook_time_minutes
    r.servings = payload.servings
    r.difficulty = payload.difficulty
    r.category = payload.category
    db.query(RecipeTag).filter(RecipeTag.recipe_id==r.id).delete()
    if payload.tag_ids:
        for tag_id in payload.tag_ids:
            tag = db.query(Tag).filter(Tag.id==tag_id, Tag.owner_id==current_user.id).first()
            if not tag:
                raise HTTPException(status_code=400, detail=f"Tag {tag_id} not found")
            db.add(RecipeTag(recipe_id=r.id, tag_id=tag.id))
    db.add(r)
    db.commit()
    db.refresh(r)
    data = RecipeOut.model_validate(r).model_dump()
    data["tags"] = [t.name for t in db.query(Tag).join(RecipeTag, RecipeTag.tag_id==Tag.id).filter(RecipeTag.recipe_id==r.id).all()]
    data["photos"] = [p.path for p in db.query(RecipePhoto).filter(RecipePhoto.recipe_id==r.id).order_by(RecipePhoto.id.asc()).all()]
    return data

@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.query(RecipeTag).filter(RecipeTag.recipe_id==r.id).delete()
    db.query(RecipePhoto).filter(RecipePhoto.recipe_id==r.id).delete()
    db.delete(r)
    db.commit()
    return {"deleted": True}

@router.post("/{recipe_id}/cook")
def start_cooking(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {
        "recipe_id": r.id,
        "title": r.title,
        "ingredients": r.ingredients,
        "instructions": r.instructions,
        "servings": r.servings,
        "prep_time_minutes": r.prep_time_minutes,
        "cook_time_minutes": r.cook_time_minutes,
        "difficulty": r.difficulty,
    }

@router.post("/{recipe_id}/photos")
def upload_recipe_photo(recipe_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    dest_dir = os.path.join("backend", "media", "recipes", str(r.id))
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported photo type")
    name = f"{int(time.time())}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(dest_dir, name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    rel = os.path.relpath(path, "backend")
    db.add(RecipePhoto(recipe_id=r.id, owner_id=current_user.id, path=rel))
    db.commit()
    return {"photo": rel}

@router.get("/export")
def export_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recipes = db.query(Recipe).filter(Recipe.owner_id==current_user.id).order_by(Recipe.created_at.desc()).all()
    tag_map = {}
    for t in db.query(Tag).filter(Tag.owner_id==current_user.id).all():
        tag_map[t.id] = t.name
    photo_map = {}
    for p in db.query(RecipePhoto).filter(RecipePhoto.owner_id==current_user.id).all():
        photo_map.setdefault(p.recipe_id, []).append(p.path)
    payload = []
    for r in recipes:
        recipe_tags = [t.name for t in db.query(Tag).join(RecipeTag, RecipeTag.tag_id==Tag.id).filter(RecipeTag.recipe_id==r.id).all()]
        payload.append({
            "title": r.title,
            "description": r.description,
            "ingredients": r.ingredients,
            "instructions": r.instructions,
            "source_url": r.source_url,
            "store": r.store.value,
            "cookbook_id": r.cookbook_id,
            "rating": r.rating,
            "prep_time_minutes": r.prep_time_minutes,
            "cook_time_minutes": r.cook_time_minutes,
            "servings": r.servings,
            "difficulty": r.difficulty,
            "category": r.category,
            "tags": recipe_tags,
            "photos": photo_map.get(r.id, []),
        })
    data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    return Response(content=data, media_type="application/json", headers={"Content-Disposition": "attachment; filename=recipes.json"})

@router.post("/import")
def import_recipes(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    content = file.file.read().decode("utf-8")
    items = json.loads(content)
    imported = 0
    for item in items:
        recipe = Recipe(
            title=item.get("title") or "Untitled",
            description=item.get("description"),
            ingredients=item.get("ingredients"),
            instructions=item.get("instructions"),
            source_url=item.get("source_url"),
            store=Store[item["store"]] if item.get("store") in {"local", "cloud"} else Store.local,
            owner_id=current_user.id,
            cookbook_id=item.get("cookbook_id"),
            rating=item.get("rating"),
            prep_time_minutes=item.get("prep_time_minutes"),
            cook_time_minutes=item.get("cook_time_minutes"),
            servings=item.get("servings"),
            difficulty=item.get("difficulty"),
            category=item.get("category"),
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        names = [str(t).strip() for t in (item.get("tags") or []) if str(t).strip()]
        for name in names:
            tag = db.query(Tag).filter(Tag.owner_id==current_user.id, Tag.name.ilike(name)).first()
            if not tag:
                tag = Tag(owner_id=current_user.id, name=name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            db.add(RecipeTag(recipe_id=recipe.id, tag_id=tag.id))
        for rel in item.get("photos") or []:
            if not rel:
                continue
            path = rel if os.path.isabs(rel) else os.path.join("backend", rel)
            if os.path.exists(path):
                db.add(RecipePhoto(recipe_id=recipe.id, owner_id=current_user.id, path=rel))
        db.commit()
        imported += 1
    return {"imported": imported}
