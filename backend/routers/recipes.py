from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Recipe, Cookbook, Tag, RecipeTag, Store
from backend.services.auth import get_current_user, require_role
from backend.schemas import RecipeCreate, RecipeOut

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
        out.append(data)
    return out

@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    data = RecipeOut.model_validate(r).model_dump()
    data["tags"] = [t.name for t in db.query(Tag).join(RecipeTag, RecipeTag.tag_id==Tag.id).filter(RecipeTag.recipe_id==r.id).all()]
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
    return data

@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recipe).filter(Recipe.id==recipe_id, Recipe.owner_id==current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.query(RecipeTag).filter(RecipeTag.recipe_id==r.id).delete()
    db.delete(r)
    db.commit()
    return {"deleted": True}
