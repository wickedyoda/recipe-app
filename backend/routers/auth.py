from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from backend.database import get_db
from backend.models import User, Role
from backend.services.auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from backend.schemas import UserCreate, UserOut, UserUpdate, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class ApproveRequest(BaseModel):
    user_id: int
    is_active: bool = True

@router.post("/register", response_model=dict)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email==payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        is_active=0,
        is_approved=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "status": "pending_approval",
        "message": "Account created. An admin must approve before login.",
    }

@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email==payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    token = create_access_token(user.email)
    return TokenOut(access_token=token, user=UserOut.model_validate(user), approved=True, active=True)

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.patch("/me", response_model=UserOut)
def update_profile(payload: UpdateProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)

@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()

@router.get("/users/pending", response_model=list[UserOut])
def pending_users(_: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_approved==0).order_by(User.created_at.desc()).all()

@router.post("/users/approve")
def approve_user(payload: ApproveRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role(Role.admin))):
    target = db.query(User).filter(User.id == payload.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_approved = 1
    target.is_active = 1 if payload.is_active else 0
    target.approved_by = current_user.id
    target.approved_at = datetime.utcnow()
    db.add(target)
    db.commit()
    db.refresh(target)
    return {"id": target.id, "email": target.email, "is_approved": bool(target.is_approved), "is_active": bool(target.is_active)}
