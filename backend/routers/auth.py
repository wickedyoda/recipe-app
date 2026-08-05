import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import GroceryList, MealPlan, Note, PasswordHistory, Recipe, Role, User
from backend.schemas import (
    AdminChangePassword,
    AdminUserCreate,
    AdminUserUpdate,
    ChangeEmailRequest,
    ChangePasswordRequest,
    PasswordResetRequest,
    ResetPasswordConfirm,
    TokenOut,
    UpdateProfileRequest,
    UserOut,
)
from backend.services.auth import (
    change_email,
    change_password,
    change_password_admin,
    consume_password_reset_token,
    create_access_token,
    get_current_user,
    hash_password,
    request_password_reset,
    require_role,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ApproveRequest(BaseModel):
    user_id: int
    is_active: bool = True


@router.post("/register", response_model=dict)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        is_active=0,
        is_approved=0,
        must_change_password=1,
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
    email = payload.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    token = create_access_token(user.email)
    return TokenOut(access_token=token, user=UserOut.model_validate(user), approved=True, active=True, must_change_password=bool(user.must_change_password))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
def update_profile(payload: UpdateProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.email is not None:
        change_email(current_user, payload.email, db)
        db.refresh(current_user)
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.post("/change-password")
def change_password_endpoint(payload: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    change_password(current_user, payload.current_password, payload.new_password, db)
    return {"ok": True, "message": "Password updated"}


@router.post("/change-email")
def change_email_endpoint(payload: ChangeEmailRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    change_email(current_user, payload.new_email, db)
    return {"ok": True, "message": "Email updated"}


@router.post("/forgot-password")
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    request_password_reset(payload.email)
    return {"ok": True, "message": "If an account exists, a reset email will be sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordConfirm, db: Session = Depends(get_db)):
    ok = consume_password_reset_token(payload.token, payload.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"ok": True, "message": "Password reset successful"}


@router.post("/me/delete")
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete own account and all associated data (GDPR right to erasure)."""
    if current_user.role == Role.admin:
        admin_count = db.query(User).filter(User.role == Role.admin).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")
    db.query(PasswordHistory).filter(PasswordHistory.user_id == current_user.id).delete(synchronize_session=False)
    db.query(User).filter(User.approved_by == current_user.id).update({"approved_by": None}, synchronize_session=False)
    db.delete(current_user)
    db.commit()
    return {"ok": True, "message": "Account and all associated data deleted"}


@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload a profile avatar image (max 1MB). Returns avatar_url for saving."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    # Validate image type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        raise HTTPException(status_code=400, detail="Only PNG, JPG, WebP, GIF allowed")
    # Check file size (read content to check)
    content = await file.read()
    if len(content) > 1024 * 1024:  # 1MB
        raise HTTPException(status_code=400, detail="Image must be under 1MB")
    # Save to media/avatars/
    avatar_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media', 'avatars')
    os.makedirs(avatar_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(avatar_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(content)
    avatar_url = f"/media/static/avatars/{filename}"
    return {"ok": True, "avatar_url": avatar_url}


@router.get("/me/export")
def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export all user data (GDPR right to data portability)."""
    user_data = {
        "user": {
            "email": current_user.email,
            "display_name": current_user.display_name,
            "role": current_user.role.value,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "recipes": [],
        "grocery_lists": [],
        "meal_plans": [],
        "notes": [],
    }
    for r in db.query(Recipe).filter(Recipe.owner_id == current_user.id).all():
        user_data["recipes"].append({
            "title": r.title,
            "description": r.description,
            "ingredients": r.ingredients,
            "instructions": r.instructions,
            "source_url": r.source_url,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    for g in db.query(GroceryList).filter(GroceryList.owner_id == current_user.id).all():
        user_data["grocery_lists"].append({"name": g.name, "created_at": g.created_at.isoformat() if g.created_at else None})
    for m in db.query(MealPlan).filter(MealPlan.owner_id == current_user.id).all():
        user_data["meal_plans"].append({"name": m.name, "period": m.period, "created_at": m.created_at.isoformat() if m.created_at else None})
    for n in db.query(Note).filter(Note.owner_id == current_user.id).all():
        user_data["notes"].append({"body": n.body, "created_at": n.created_at.isoformat() if n.created_at else None})
    return JSONResponse(user_data, headers={"Content-Disposition": "attachment; filename=user-data-export.json"})


@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/users/pending", response_model=list[UserOut])
def pending_users(_: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_approved == 0).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserOut)
def create_user(payload: AdminUserCreate, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    role = Role.user
    if payload.role and payload.role in Role.__members__:
        role = Role(payload.role)
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        role=role,
        is_active=1 if payload.is_active else 0,
        is_approved=1 if payload.is_approved else 0,
        must_change_password=0,
        password_changed_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    """Get a single user by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: AdminUserUpdate, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role is not None:
        if payload.role not in Role.__members__:
            raise HTTPException(status_code=400, detail="Invalid role")
        target.role = Role(payload.role)
    if payload.is_active is not None:
        target.is_active = 1 if payload.is_active else 0
    if payload.is_approved is not None:
        target.is_approved = 1 if payload.is_approved else 0
        if payload.is_approved:
            target.approved_at = datetime.utcnow()
    if payload.display_name is not None:
        target.display_name = payload.display_name
    if payload.must_change_password is not None:
        target.must_change_password = 1 if payload.must_change_password else 0
    db.add(target)
    db.commit()
    db.refresh(target)
    return UserOut.model_validate(target)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role == Role.admin:
        admin_count = db.query(User).filter(User.role == Role.admin).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")
    db.query(PasswordHistory).filter(PasswordHistory.user_id == user_id).delete(synchronize_session=False)
    db.query(User).filter(User.approved_by == user_id).update({"approved_by": None}, synchronize_session=False)
    db.delete(target)
    db.commit()
    return {"ok": True, "message": "User deleted"}


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


@router.patch("/users/{user_id}/role")
def change_user_role(user_id: int, payload: AdminUserUpdate, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role is None:
        raise HTTPException(status_code=400, detail="Role is required")
    if payload.role not in Role.__members__:
        raise HTTPException(status_code=400, detail="Invalid role")
    target.role = Role(payload.role)
    db.add(target)
    db.commit()
    db.refresh(target)
    return {"id": target.id, "email": target.email, "role": target.role.value}


@router.patch("/users/{user_id}/password")
def admin_change_password(user_id: int, payload: AdminChangePassword, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    change_password_admin(target, payload.new_password, db)
    return {"ok": True, "message": "Password updated"}


@router.patch("/users/{user_id}/approve")
def approve_user_patch(user_id: int, _: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_approved = 1
    target.is_active = 1
    target.approved_at = datetime.utcnow()
    db.add(target)
    db.commit()
    db.refresh(target)
    return {"id": target.id, "email": target.email, "is_approved": True, "is_active": True}
