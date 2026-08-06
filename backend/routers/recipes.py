import json
import os
import secrets
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy import func as _func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Cookbook,
    Recipe,
    RecipeMedia,
    RecipePhoto,
    RecipeRating,
    RecipeStepPhoto,
    RecipeTag,
    Store,
    Tag,
    User,
    household_members,
    household_recipes,
)
from backend.schemas import RecipeCreate, RecipeOut
from backend.services.auth import get_current_user

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("", response_model=RecipeOut)
def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Prevent duplicates: same name + first 5 words of description for same user
    desc_first_5 = ' '.join((payload.description or '').split()[:5])
    existing_recipes = db.query(Recipe).filter(
        Recipe.owner_id == current_user.id,
        Recipe.title == payload.title.strip()
    ).all()
    for ex in existing_recipes:
        ex_desc_first_5 = ' '.join((ex.description or '').split()[:5])
        if ex_desc_first_5 == desc_first_5:
            raise HTTPException(status_code=409, detail=f"A recipe with this title and description already exists (ID: {ex.id})")
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
        flavor_rating=payload.flavor_rating,
        effort_rating=payload.effort_rating,
        prep_time_minutes=payload.prep_time_minutes,
        cook_time_minutes=payload.cook_time_minutes,
        servings=payload.servings,
        difficulty=payload.difficulty,
        category=payload.category,
        subcategory=payload.subcategory,
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
def list_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), q: str = "", limit: int = 200):
    rows = db.query(Recipe).filter(Recipe.owner_id==current_user.id)
    # Also include recipes shared with the user's household
    household_subq = (
        db.query(household_recipes.c.recipe_id)
        .join(household_members, household_members.c.household_id == household_recipes.c.household_id)
        .filter(household_members.c.user_id == current_user.id)
        .subquery()
    )
    rows = db.query(Recipe).filter(
        (Recipe.owner_id == current_user.id) | (Recipe.id.in_(household_subq))
    )
    if q:
        # Search recipe title, description, ingredients, instructions, AND extracted media text
        media_subq = db.query(RecipeMedia.recipe_id).filter(
            RecipeMedia.owner_id == current_user.id,
            RecipeMedia.extracted_text.is_not(None),
            RecipeMedia.extracted_text.like(f"%{q}%"),
        ).subquery()
        rows = rows.filter(
            (Recipe.title.ilike(f"%{q}%"))
            | (Recipe.description.ilike(f"%{q}%"))
            | (Recipe.ingredients.ilike(f"%{q}%"))
            | (Recipe.instructions.ilike(f"%{q}%"))
            | (Recipe.id.in_(media_subq))
        )
    rows = rows.order_by(Recipe.created_at.desc()).limit(limit).all()
    recipe_ids = [r.id for r in rows]
    # Batch query cookbook names
    cb_rows = db.query(Cookbook).filter(Cookbook.owner_id == current_user.id).all()
    cb_map = {cb.id: cb.name for cb in cb_rows}
    # Batch queries to avoid N+1
    tag_results = db.query(RecipeTag.recipe_id, Tag.name).join(Tag, Tag.id==RecipeTag.tag_id).filter(RecipeTag.recipe_id.in_(recipe_ids)).all()
    recipe_tags = {}
    for rid, tname in tag_results:
        recipe_tags.setdefault(rid, []).append(tname)
    photo_results = db.query(RecipePhoto.recipe_id, RecipePhoto.path).filter(RecipePhoto.recipe_id.in_(recipe_ids)).order_by(RecipePhoto.id.asc()).all()
    recipe_photos = {}
    for rid, path in photo_results:
        recipe_photos.setdefault(rid, []).append(path)
    # Batch query ratings
    rating_results = db.query(RecipeRating.recipe_id, _func.avg(RecipeRating.score).label('avg'), _func.count(RecipeRating.score).label('cnt')).filter(RecipeRating.recipe_id.in_(recipe_ids)).group_by(RecipeRating.recipe_id).all()
    recipe_avg_ratings = {rid: float(avg) for rid, avg, cnt in rating_results}
    recipe_rating_counts = {rid: cnt for rid, avg, cnt in rating_results}
    user_rating_results = db.query(RecipeRating.recipe_id, RecipeRating.score).filter(RecipeRating.recipe_id.in_(recipe_ids), RecipeRating.user_id == current_user.id).all()
    user_ratings = {rid: score for rid, score in user_rating_results}
    out = []
    for r in rows:
        data = RecipeOut.model_validate(r).model_dump()
        data["cookbook_name"] = cb_map.get(r.cookbook_id) if r.cookbook_id else None
        data["tags"] = recipe_tags.get(r.id, [])
        data["photos"] = recipe_photos.get(r.id, [])
        data["rating"] = recipe_avg_ratings.get(r.id)  # average rating
        data["rating_count"] = recipe_rating_counts.get(r.id, 0)
        data["user_rating"] = user_ratings.get(r.id)
        out.append(data)
    return out

@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        # Check if recipe is shared with user's household
        shared_subq = (
            db.query(household_recipes.c.recipe_id)
            .join(household_members, household_members.c.household_id == household_recipes.c.household_id)
            .filter(household_members.c.user_id == current_user.id)
        )
        r = db.query(Recipe).filter(
            Recipe.id == recipe_id,
            Recipe.id.in_(shared_subq)
        ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    data = RecipeOut.model_validate(r).model_dump()
    data["tags"] = [t.name for t in db.query(Tag).join(RecipeTag, RecipeTag.tag_id==Tag.id).filter(RecipeTag.recipe_id==r.id).all()]
    data["photos"] = [p.path for p in db.query(RecipePhoto).filter(RecipePhoto.recipe_id==r.id).order_by(RecipePhoto.id.asc()).all()]
    data["step_photos"] = [{"step_index": s.step_index, "path": s.path, "caption": s.caption} for s in db.query(RecipeStepPhoto).filter(RecipeStepPhoto.recipe_id==r.id).order_by(RecipeStepPhoto.step_index.asc()).all()]
    data["media"] = [{"id": m.id, "file_path": m.file_path, "thumbnail_path": m.thumbnail_path, "original_filename": m.original_filename, "media_type": m.media_type, "file_size": m.file_size, "has_text": bool(m.extracted_text)} for m in db.query(RecipeMedia).filter(RecipeMedia.recipe_id==r.id).order_by(RecipeMedia.created_at.desc()).all()]
    # Add rating info
    avg_rating = db.query(_func.avg(RecipeRating.score)).filter(RecipeRating.recipe_id==r.id).scalar()
    rating_count = db.query(_func.count(RecipeRating.score)).filter(RecipeRating.recipe_id==r.id).scalar()
    user_rating = db.query(RecipeRating.score).filter(RecipeRating.recipe_id==r.id, RecipeRating.user_id==current_user.id).scalar()
    data["rating"] = float(avg_rating) if avg_rating else None
    data["rating_count"] = rating_count or 0
    data["user_rating"] = user_rating
    return data


@router.post("/{recipe_id}/rate")
def rate_recipe(recipe_id: int, score: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if score < 0 or score > 5:
        raise HTTPException(status_code=400, detail="Score must be 0-5")
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    existing = db.query(RecipeRating).filter(RecipeRating.recipe_id==r.id, RecipeRating.user_id==current_user.id).first()
    if existing:
        existing.score = score
    else:
        db.add(RecipeRating(recipe_id=r.id, user_id=current_user.id, score=score))
    db.commit()
    # Update average rating on recipe
    avg = db.query(_func.avg(RecipeRating.score)).filter(RecipeRating.recipe_id==r.id).scalar()
    r.rating = float(avg) if avg else None
    db.commit()
    return {"ok": True, "rating": float(avg) if avg else None, "score": score}

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
    r.household_id = payload.household_id
    r.rating = payload.rating
    r.flavor_rating = payload.flavor_rating
    r.effort_rating = payload.effort_rating
    r.prep_time_minutes = payload.prep_time_minutes
    r.cook_time_minutes = payload.cook_time_minutes
    r.servings = payload.servings
    r.difficulty = payload.difficulty
    r.category = payload.category
    r.subcategory = payload.subcategory
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

@router.post("/{recipe_id}/share")
def share_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if not r.share_token:
        r.share_token = secrets.token_urlsafe(16)
        db.add(r)
        db.commit()
        db.refresh(r)
    public_url = (os.getenv("PUBLIC_URL") or "").rstrip("/")
    link = (public_url + "/recipes/public/" + r.share_token) if public_url else ("/recipes/public/" + r.share_token)
    return {"share_token": r.share_token, "public_url": link, "shared": True}

@router.get("/public/{share_token}")
def public_recipe(share_token: str, db: Session = Depends(get_db)):
    r = db.query(Recipe).filter(Recipe.share_token==share_token).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    avg_rating = db.query(_func.avg(RecipeRating.score)).filter(RecipeRating.recipe_id==r.id).scalar()
    rating_count = db.query(_func.count(RecipeRating.score)).filter(RecipeRating.recipe_id==r.id).scalar()
    # Public-safe response: no user data, notes, source_path, personal info
    return {
        "title": r.title,
        "description": r.description,
        "ingredients": r.ingredients,
        "instructions": r.instructions,
        "servings": r.servings,
        "prep_time_minutes": r.prep_time_minutes,
        "cook_time_minutes": r.cook_time_minutes,
        "difficulty": r.difficulty,
        "category": r.category,
        "subcategory": r.subcategory,
        "rating": float(avg_rating) if avg_rating else None,
        "rating_count": rating_count,
        "created_at": r.created_at.isoformat() if r.created_at else None,
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

@router.post("/{recipe_id}/step-photos")
def upload_step_photo(recipe_id: int, step_index: int = 0, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    dest_dir = os.path.join("backend", "media", "recipes", str(r.id), "steps")
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported photo type")
    name = f"step{step_index}_{int(time.time())}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(dest_dir, name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    rel = os.path.relpath(path, "backend")
    db.add(RecipeStepPhoto(recipe_id=r.id, owner_id=current_user.id, step_index=max(0, int(step_index or 0)), path=rel))
    db.commit()
    return {"step_photo": rel}

@router.get("/export")
def export_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recipes = db.query(Recipe).filter(Recipe.owner_id==current_user.id).order_by(Recipe.created_at.desc()).all()
    sel_ids = [r.id for r in recipes]
    # Batch queries to avoid N+1
    tag_name_results = db.query(RecipeTag.recipe_id, Tag.name).join(Tag, Tag.id==RecipeTag.tag_id).filter(RecipeTag.recipe_id.in_(sel_ids)).all()
    recipe_tag_map = {}
    for rid, tname in tag_name_results:
        recipe_tag_map.setdefault(rid, []).append(tname)
    photo_results = db.query(RecipePhoto.recipe_id, RecipePhoto.path).filter(RecipePhoto.recipe_id.in_(sel_ids)).order_by(RecipePhoto.id.asc()).all()
    recipe_photo_map = {}
    for rid, path in photo_results:
        recipe_photo_map.setdefault(rid, []).append(path)
    payload = []
    for r in recipes:
        recipe_tags = recipe_tag_map.get(r.id, [])
        payload.append({
            "title": r.title,
            "description": r.description,
            "ingredients": r.ingredients,
            "instructions": r.instructions,
            "source_url": r.source_url,
            "store": r.store.value,
            "cookbook_id": r.cookbook_id,
            "rating": r.rating,
            "flavor_rating": r.flavor_rating,
            "effort_rating": r.effort_rating,
            "prep_time_minutes": r.prep_time_minutes,
            "cook_time_minutes": r.cook_time_minutes,
            "servings": r.servings,
            "difficulty": r.difficulty,
            "category": r.category,
            "subcategory": r.subcategory,
            "tags": recipe_tags,
            "photos": recipe_photo_map.get(r.id, []),
        })
    data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    return Response(content=data, media_type="application/json", headers={"Content-Disposition": "attachment; filename=recipes.json"})

@router.post("/export-selected")
async def export_selected(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    body = await request.body()
    data = json.loads(body)
    ids = data.get("ids", [])
    if not ids:
        return Response(content=b'[]', media_type="application/json")
    recipes = db.query(Recipe).filter(Recipe.id.in_(ids), Recipe.owner_id==current_user.id).all()
    sel_ids = [r.id for r in recipes]
    # Batch queries to avoid N+1
    tag_name_results = db.query(RecipeTag.recipe_id, Tag.name).join(Tag, Tag.id==RecipeTag.tag_id).filter(RecipeTag.recipe_id.in_(sel_ids)).all()
    recipe_tag_map = {}
    for rid, tname in tag_name_results:
        recipe_tag_map.setdefault(rid, []).append(tname)
    photo_results = db.query(RecipePhoto.recipe_id, RecipePhoto.path).filter(RecipePhoto.recipe_id.in_(sel_ids)).order_by(RecipePhoto.id.asc()).all()
    recipe_photo_map = {}
    for rid, path in photo_results:
        recipe_photo_map.setdefault(rid, []).append(path)
    payload = []
    for r in recipes:
        recipe_tags = recipe_tag_map.get(r.id, [])
        payload.append({
            "title": r.title,
            "description": r.description,
            "ingredients": r.ingredients,
            "instructions": r.instructions,
            "source_url": r.source_url,
            "store": r.store.value,
            "cookbook_id": r.cookbook_id,
            "rating": r.rating,
            "flavor_rating": r.flavor_rating,
            "effort_rating": r.effort_rating,
            "prep_time_minutes": r.prep_time_minutes,
            "cook_time_minutes": r.cook_time_minutes,
            "servings": r.servings,
            "difficulty": r.difficulty,
            "category": r.category,
            "subcategory": r.subcategory,
            "tags": recipe_tags,
            "photos": recipe_photo_map.get(r.id, []),
        })
    out = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    return Response(content=out, media_type="application/json", headers={"Content-Disposition": "attachment; filename=recipes-selected.json"})
