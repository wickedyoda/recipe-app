from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Cookbook, Recipe, User
from backend.schemas import CookbookCreate, CookbookOut
from backend.services.auth import get_current_user

router = APIRouter(prefix="/cookbooks", tags=["cookbooks"])


@router.get("/", response_model=list[CookbookOut])
def list_cookbooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all cookbooks owned by the current user."""
    return (
        db.query(Cookbook)
        .filter(Cookbook.owner_id == current_user.id)
        .order_by(Cookbook.name)
        .all()
    )


@router.post("/", response_model=CookbookOut)
def create_cookbook(
    payload: CookbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new cookbook."""
    cb = Cookbook(
        name=payload.name,
        description=payload.description,
        store=payload.store or "local",
        owner_id=current_user.id,
    )
    db.add(cb)
    db.commit()
    db.refresh(cb)
    return cb


@router.get("/{cookbook_id}/recipes", response_model=list[dict])
def get_cookbook_recipes(
    cookbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all recipes in a cookbook with their basic info."""
    cb = (
        db.query(Cookbook)
        .filter(Cookbook.id == cookbook_id, Cookbook.owner_id == current_user.id)
        .first()
    )
    if not cb:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    recipes = (
        db.query(Recipe)
        .filter(Recipe.cookbook_id == cookbook_id, Recipe.owner_id == current_user.id)
        .order_by(Recipe.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "category": r.category,
            "difficulty": r.difficulty,
        }
        for r in recipes
    ]


@router.patch("/{cookbook_id}", response_model=CookbookOut)
def update_cookbook(
    cookbook_id: int,
    payload: CookbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a cookbook's name and description."""
    cb = (
        db.query(Cookbook)
        .filter(Cookbook.id == cookbook_id, Cookbook.owner_id == current_user.id)
        .first()
    )
    if not cb:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    cb.name = payload.name
    cb.description = payload.description
    db.commit()
    db.refresh(cb)
    return cb


@router.delete("/{cookbook_id}")
def delete_cookbook(
    cookbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a cookbook. Recipes are moved to the default 'Imported Recipes' cookbook."""
    cb = (
        db.query(Cookbook)
        .filter(Cookbook.id == cookbook_id, Cookbook.owner_id == current_user.id)
        .first()
    )
    if not cb:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    # Move recipes to a default cookbook if this is not the only one
    default = (
        db.query(Cookbook)
        .filter(Cookbook.owner_id == current_user.id, Cookbook.name != cb.name)
        .first()
    )
    if default:
        db.query(Recipe).filter(
            Recipe.cookbook_id == cookbook_id,
            Recipe.owner_id == current_user.id,
        ).update({"cookbook_id": default.id})
    else:
        # Delete recipes if no other cookbook exists
        db.query(Recipe).filter(
            Recipe.cookbook_id == cookbook_id,
            Recipe.owner_id == current_user.id,
        ).delete(synchronize_session=False)
    db.delete(cb)
    db.commit()
    return {"ok": True, "message": "Cookbook deleted"}
