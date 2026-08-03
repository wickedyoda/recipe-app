from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_approved: bool
    approved_at: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    approved: bool = False
    active: bool = False

class CookbookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    store: Optional[str] = "local"

class CookbookOut(CookbookCreate):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    store: Optional[str] = "local"
    cookbook_id: Optional[int] = None
    rating: Optional[float] = None
    tag_ids: Optional[List[int]] = None

class RecipeOut(RecipeCreate):
    id: int
    owner_id: int
    created_at: datetime
    tags: List[str] = []
    class Config:
        from_attributes = True

class IngestRequest(BaseModel):
    url: str

class MediaItem(BaseModel):
    id: int
    title: str
    source_url: Optional[str]
    source_path: Optional[str]
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class NoteCreate(BaseModel):
    body: str
    recipe_id: int

class NoteOut(NoteCreate):
    id: int
    recipe_id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TagCreate(BaseModel):
    name: str

class TagOut(TagCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class MealPlanCreate(BaseModel):
    name: str
    period: str

class MealPlanOut(MealPlanCreate):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class MealPlanEntryCreate(BaseModel):
    meal_plan_id: int
    recipe_id: int
    meal: str
    date: Optional[str] = None

class MealPlanEntryOut(MealPlanEntryCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class GroceryListCreate(BaseModel):
    name: str

class GroceryListOut(GroceryListCreate):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class GroceryItemCreate(BaseModel):
    list_id: int
    recipe_id: Optional[int] = None
    name: str
    quantity: Optional[str] = None

class GroceryItemOut(GroceryItemCreate):
    id: int
    checked: bool
    owner_id: int
    class Config:
        from_attributes = True
