from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func as _func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Household, Recipe, RecipeRating, User, household_members, household_recipes
from backend.schemas import HouseholdCreate, HouseholdOut
from backend.services.auth import get_current_user

router = APIRouter(prefix="/households", tags=["households"])

MAX_MEMBERS = 7


@router.get("/", response_model=list[HouseholdOut])
def list_households(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get households where user is a member (via association table)
    rows = (
        db.query(Household)
        .join(household_members, household_members.c.household_id == Household.id)
        .filter(household_members.c.user_id == current_user.id)
        .all()
    )
    result = []
    for h in rows:
        shared_count = db.execute(
            _func.count().select().where(household_recipes.c.household_id == h.id)
        ).scalar()
        member_count = db.execute(
            _func.count().select().where(household_members.c.household_id == h.id)
        ).scalar()
        members_data = []
        member_rows = (
            db.query(User)
            .join(household_members, household_members.c.user_id == User.id)
            .filter(household_members.c.household_id == h.id)
            .all()
        )
        for m in member_rows:
            members_data.append({
                "id": m.id,
                "email": m.email,
                "display_name": m.display_name,
                "avatar_url": m.avatar_url,
            })
        result.append({
            "id": h.id,
            "name": h.name,
            "avatar_url": h.avatar_url,
            "owner_id": h.owner_id,
            "created_at": h.created_at,
            "member_count": member_count,
            "shared_recipe_count": shared_count,
            "members": members_data,
        })
    return result


@router.post("/", response_model=HouseholdOut)
def create_household(payload: HouseholdCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if user is already a member of a household
    existing = (
        db.query(household_members)
        .filter(household_members.c.user_id == current_user.id)
        .first()
    )
    if existing:
        # Check if they're the owner or just a member
        h = db.query(Household).filter(Household.id == existing.household_id).first()
        if h and h.owner_id == current_user.id:
            raise HTTPException(status_code=400, detail="You already own a household")
        if h:
            raise HTTPException(status_code=400, detail=f"You are already a member of '{h.name}'. You can only be in one household at a time.")

    household = Household(name=payload.name, avatar_url=payload.avatar_url, owner_id=current_user.id)
    db.add(household)
    db.commit()
    db.refresh(household)

    # Add owner as first member (doesn't count against the 7 limit — owner is separate)
    db.execute(
        household_members.insert().values(
            household_id=household.id,
            user_id=current_user.id,
            role="owner",
        )
    )
    db.commit()
    return {
        "id": household.id,
        "name": household.name,
        "avatar_url": household.avatar_url,
        "owner_id": household.owner_id,
        "created_at": household.created_at,
        "member_count": 1,
        "shared_recipe_count": 0,
        "members": [{"id": current_user.id, "email": current_user.email, "display_name": current_user.display_name, "avatar_url": current_user.avatar_url}],
    }


@router.get("/{household_id}", response_model=HouseholdOut)
def get_household(household_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    # Check membership
    membership = db.execute(
        household_members.select().where(
            household_members.c.household_id == household_id,
            household_members.c.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this household")

    shared_count = db.execute(
        _func.count().select().where(household_recipes.c.household_id == household_id)
    ).scalar()
    member_count = db.execute(
        _func.count().select().where(household_members.c.household_id == household_id)
    ).scalar()
    member_rows = (
        db.query(User)
        .join(household_members, household_members.c.user_id == User.id)
        .filter(household_members.c.household_id == household_id)
        .all()
    )
    members_data = []
    for m in member_rows:
        members_data.append({
            "id": m.id,
            "email": m.email,
            "display_name": m.display_name,
            "avatar_url": m.avatar_url,
        })
    return {
        "id": h.id,
        "name": h.name,
        "avatar_url": h.avatar_url,
        "owner_id": h.owner_id,
        "created_at": h.created_at,
        "member_count": member_count,
        "shared_recipe_count": shared_count,
        "members": members_data,
    }


@router.delete("/{household_id}")
def delete_household(household_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    if h.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the household owner can delete the household")
    db.delete(h)
    db.commit()
    return {"ok": True, "message": "Household deleted"}


@router.post("/{household_id}/invite")
def invite_member(household_id: int, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    if h.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the household owner can invite members")

    email = payload.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. They must have an account.")

    # Check already a member
    existing = db.execute(
        household_members.select().where(
            household_members.c.household_id == household_id,
            household_members.c.user_id == user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this household")

    # Check max 7 members (not counting owner? Actually owner IS a member)
    member_count = db.execute(
        _func.count().select().where(household_members.c.household_id == household_id)
    ).scalar()
    if member_count >= MAX_MEMBERS:
        raise HTTPException(status_code=400, detail=f"A household can have at most {MAX_MEMBERS} members")

    role = payload.get("role", "member")
    db.execute(
        household_members.insert().values(
            household_id=household_id,
            user_id=user.id,
            role=role,
        )
    )
    db.commit()
    return {"ok": True, "message": f"Invited {user.display_name or user.email} to the household"}


@router.delete("/{household_id}/members/{user_id}")
def remove_member(household_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    if h.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the household owner can remove members")
    if user_id == h.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove the household owner")

    result = db.execute(
        household_members.delete().where(
            household_members.c.household_id == household_id,
            household_members.c.user_id == user_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Member not found in this household")
    db.commit()
    return {"ok": True, "message": "Member removed from household"}


@router.post("/{household_id}/share-recipe/{recipe_id}")
def share_recipe_to_household(household_id: int, recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    # Only owner or member can share
    membership = db.execute(
        household_members.select().where(
            household_members.c.household_id == household_id,
            household_members.c.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this household")

    r = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.owner_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found or not owned by you")

    # Check if already shared
    existing = db.execute(
        household_recipes.select().where(
            household_recipes.c.household_id == household_id,
            household_recipes.c.recipe_id == recipe_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Recipe is already shared with this household")

    db.execute(
        household_recipes.insert().values(
            household_id=household_id,
            recipe_id=recipe_id,
        )
    )
    db.commit()
    return {"ok": True, "message": "Recipe shared with household"}


@router.delete("/{household_id}/share-recipe/{recipe_id}")
def unshare_recipe_from_household(household_id: int, recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    membership = db.execute(
        household_members.select().where(
            household_members.c.household_id == household_id,
            household_members.c.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this household")

    result = db.execute(
        household_recipes.delete().where(
            household_recipes.c.household_id == household_id,
            household_recipes.c.recipe_id == recipe_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Recipe is not shared with this household")
    db.commit()
    return {"ok": True, "message": "Recipe unshared from household"}


@router.get("/{household_id}/recipes")
def get_household_recipes(household_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Household).filter(Household.id == household_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    membership = db.execute(
        household_members.select().where(
            household_members.c.household_id == household_id,
            household_members.c.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this household")

    # Get recipes shared with this household
    recipe_ids = [
        row[0] for row in db.execute(
            household_recipes.select().where(household_recipes.c.household_id == household_id)
        ).fetchall()
    ]
    if not recipe_ids:
        return []

    recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).order_by(Recipe.created_at.desc()).all()
    recipe_ids_list = [r.id for r in recipes]
    # Batch rating query
    rating_results = (
        db.query(RecipeRating.recipe_id, _func.avg(RecipeRating.score), _func.count(RecipeRating.score))
        .filter(RecipeRating.recipe_id.in_(recipe_ids_list))
        .group_by(RecipeRating.recipe_id)
        .all()
    )
    avg_ratings = {rid: float(avg) for rid, avg, cnt in rating_results}
    rating_counts = {rid: cnt for rid, avg, cnt in rating_results}

    result = []
    for r in recipes:
        result.append({
            "id": r.id,
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
            "rating": avg_ratings.get(r.id),
            "rating_count": rating_counts.get(r.id, 0),
            "owner_id": r.owner_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result
