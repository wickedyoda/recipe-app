from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(value) > 12:
            raise ValueError("Password must be no more than 12 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in value):
            raise ValueError("Password must contain at least 1 symbol")
        return value


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    display_name: str | None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    avatar_url: str | None
    is_active: bool
    is_approved: bool
    approved_at: datetime | None
    created_at: datetime
    must_change_password: bool = False
    is_readonly: bool = False
    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    avatar_url: str | None = None
    is_active: bool | None = None
    is_approved: bool | None = None


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    is_approved: bool | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    must_change_password: bool | None = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    role: str | None = "user"
    is_active: bool = True
    is_approved: bool = True

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(value) > 12:
            raise ValueError("Password must be no more than 12 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in value):
            raise ValueError("Password must contain at least 1 symbol")
        return value


class AdminChangePassword(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(value) > 12:
            raise ValueError("Password must be no more than 12 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in value):
            raise ValueError("Password must contain at least 1 symbol")
        return value


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(value) > 12:
            raise ValueError("Password must be no more than 12 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in value):
            raise ValueError("Password must contain at least 1 symbol")
        return value


class PasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(value) > 12:
            raise ValueError("Password must be no more than 12 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in value):
            raise ValueError("Password must contain at least 1 symbol")
        return value


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    approved: bool = False
    active: bool = False
    must_change_password: bool = False


class CookbookCreate(BaseModel):
    name: str
    description: str | None = None
    store: str | None = "local"


class CookbookOut(CookbookCreate):
    id: int
    owner_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    title: str
    description: str | None = None
    ingredients: str | None = None
    instructions: str | None = None
    source_url: str | None = None
    source_path: str | None = None
    store: str | None = "local"
    cookbook_id: int | None = None
    household_id: int | None = None
    rating: float | None = None
    flavor_rating: float | None = None
    effort_rating: float | None = None
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
    media: list = []
    rating_count: int = 0
    user_rating: int | None = None
    model_config = {"from_attributes": True}


class IngestRequest(BaseModel):
    url: str


class MediaItem(BaseModel):
    id: int
    title: str
    source_url: str | None
    source_path: str | None
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class RecipeMediaItem(BaseModel):
    id: int
    recipe_id: int
    file_path: str
    thumbnail_path: str | None
    original_filename: str
    media_type: str
    file_size: int | None
    extracted_text: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class RecipeMediaCreate(BaseModel):
    pass


class NoteCreate(BaseModel):
    body: str
    recipe_id: int


class NoteOut(NoteCreate):
    id: int
    recipe_id: int
    owner_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str


class TagOut(TagCreate):
    id: int
    owner_id: int
    model_config = {"from_attributes": True}


class MealPlanCreate(BaseModel):
    name: str
    period: str


class MealPlanOut(MealPlanCreate):
    id: int
    owner_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class MealPlanEntryCreate(BaseModel):
    meal_plan_id: int
    recipe_id: int
    meal: str
    date: str | None = None
    position: int = 0


class MealPlanEntryOut(MealPlanEntryCreate):
    id: int
    owner_id: int
    model_config = {"from_attributes": True}


class GroceryListCreate(BaseModel):
    name: str


class GroceryListOut(GroceryListCreate):
    id: int
    owner_id: int
    share_token: str | None
    share_enabled: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


class GroceryItemCreate(BaseModel):
    list_id: int
    recipe_id: int | None = None
    name: str
    quantity: str | None = None


class GroceryItemBulkCreate(BaseModel):
    items: list[GroceryItemCreate]


class GroceryItemOut(GroceryItemCreate):
    id: int
    checked: bool
    owner_id: int
    model_config = {"from_attributes": True}


class HouseholdCreate(BaseModel):
    name: str
    avatar_url: str | None = None

class HouseholdOut(BaseModel):
    id: int
    name: str
    avatar_url: str | None = None
    owner_id: int
    created_at: datetime
    member_count: int = 0
    members: list = []
    model_config = {"from_attributes": True}

class HouseholdMemberAdd(BaseModel):
    email: str
    role: str = "member"

