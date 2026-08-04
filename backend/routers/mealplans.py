from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import MealPlan, MealPlanEntry, Recipe, User
from backend.schemas import (
    MealPlanCreate,
    MealPlanEntryCreate,
    MealPlanEntryOut,
    MealPlanOut,
)
from backend.services.auth import get_current_user

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])

@router.post("", response_model=MealPlanOut)
def create_meal_plan(payload: MealPlanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = MealPlan(name=payload.name, period=payload.period, owner_id=current_user.id)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return MealPlanOut.model_validate(plan)

@router.get("", response_model=list[MealPlanOut])
def list_meal_plans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(MealPlan).filter(MealPlan.owner_id==current_user.id).order_by(MealPlan.created_at.desc()).all()

@router.get("/{plan_id}", response_model=MealPlanOut)
def get_meal_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.query(MealPlan).filter(MealPlan.id==plan_id, MealPlan.owner_id==current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return MealPlanOut.model_validate(plan)

@router.post("/entries", response_model=MealPlanEntryOut)
def create_entry(payload: MealPlanEntryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.query(MealPlan).filter(MealPlan.id==payload.meal_plan_id, MealPlan.owner_id==current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    recipe = db.query(Recipe).filter(Recipe.id==payload.recipe_id, Recipe.owner_id==current_user.id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    entry = MealPlanEntry(meal_plan_id=plan.id, recipe_id=recipe.id, meal=payload.meal, date=payload.date, owner_id=current_user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return MealPlanEntryOut.model_validate(entry)

@router.get("/{plan_id}/entries", response_model=list[MealPlanEntryOut])
def list_entries(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.query(MealPlan).filter(MealPlan.id==plan_id, MealPlan.owner_id==current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return db.query(MealPlanEntry).filter(MealPlanEntry.meal_plan_id==plan_id).order_by(MealPlanEntry.position.asc()).all()

@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(MealPlanEntry).filter(MealPlanEntry.id==entry_id, MealPlanEntry.owner_id==current_user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Meal plan entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": True}

class ReorderPayload(BaseModel):
    positions: list[dict]

@router.patch("/entries/reorder", response_model=list[MealPlanEntryOut])
def reorder_entries(payload: ReorderPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for item in payload.positions:
        entry = db.query(MealPlanEntry).filter(MealPlanEntry.id==item["id"], MealPlanEntry.owner_id==current_user.id).first()
        if entry:
            entry.position = item["position"]
    db.commit()
    plan_id = payload.positions[0]["id"] if payload.positions else 0
    if plan_id:
        real_plan = db.query(MealPlanEntry).filter(MealPlanEntry.id==plan_id).first()
        if real_plan:
            return db.query(MealPlanEntry).filter(MealPlanEntry.meal_plan_id==real_plan.meal_plan_id).order_by(MealPlanEntry.position.asc()).all()
    return []
