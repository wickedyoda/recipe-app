from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class CookbookBase(BaseModel):
    name: str
    description: Optional[str] = None
    store: Optional[str] = "local"

class CookbookCreate(CookbookBase):
    pass

class CookbookOut(CookbookBase):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    store: Optional[str] = "local"
    cookbook_id: Optional[int] = None

class RecipeCreate(RecipeBase):
    pass

class RecipeOut(RecipeBase):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True
