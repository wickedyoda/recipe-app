from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

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
    created_at: datetime
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

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

class RecipeOut(RecipeCreate):
    id: int
    owner_id: int
    created_at: datetime
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
