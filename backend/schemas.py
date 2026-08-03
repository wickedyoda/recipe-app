from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    display_name: str | None
    avatar_url: str | None
    is_active: bool
    is_approved: bool
    approved_at: datetime | None
    created_at: datetime
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None
    is_approved: bool | None = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    approved: bool = False
    active: bool = False

class CookbookCreate(BaseModel):
    name: str
    description: str | None = None
    store: str | None = "local"

class CookbookOut(CookbookCreate):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RecipeCreate(BaseModel):
    title: str
    description: str | None = None
    ingredients: str | None = None
    instructions: str | None = None
    source_url: str | None = None
    source_path: str | None = None
    store: str | None = "local"
    cookbook_id: int | None = None
    rating: float | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int | None = None
    difficulty: str | None = None
    category: str | None = None
    subcategory: str | None = None
    tag_ids: list[int] | None = None

class RecipeOut(RecipeCreate):
    id: int
    owner_id: int
    created_at: datetime
    tags: list[str] = []
    photos: list[str] = []
    step_photos: list[dict] = []
    class Config:
        from_attributes = True

class IngestRequest(BaseModel):
    url: str

class MediaItem(BaseModel):
    id: int
    title: str
    source_url: str | None
    source_path: str | None
    description: str | None
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
    date: str | None = None

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
    share_token: str | None
    share_enabled: bool = False
    created_at: datetime
    class Config:
        from_attributes = True

class GroceryItemCreate(BaseModel):
    list_id: int
    recipe_id: int | None = None
    name: str
    quantity: str | None = None

class GroceryItemOut(GroceryItemCreate):
    id: int
    checked: bool
    owner_id: int
    class Config:
        from_attributes = True
