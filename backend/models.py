import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from backend.database import Base


class Store(str, enum.Enum):
    local = "local"
    cloud = "cloud"

class Role(str, enum.Enum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role), default=Role.user, nullable=False)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    is_active = Column(Integer, default=0, nullable=False)
    is_approved = Column(Integer, default=0, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Cookbook(Base):
    __tablename__ = "cookbooks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    store = Column(Enum(Store), default=Store.local, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    source_url = Column(String(1024), nullable=True)
    source_path = Column(String(1024), nullable=True)
    store = Column(Enum(Store), default=Store.local, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cookbook_id = Column(Integer, ForeignKey("cookbooks.id"), nullable=True)
    rating = Column(Float, nullable=True)
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    difficulty = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecipeTag(Base):
    __tablename__ = "recipe_tags"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)

class RecipePhoto(Base):
    __tablename__ = "recipe_photos"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path = Column(String(1024), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MealPlan(Base):
    __tablename__ = "meal_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    period = Column(String(50), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MealPlanEntry(Base):
    __tablename__ = "meal_plan_entries"
    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    meal = Column(String(50), nullable=False)
    date = Column(String(20), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class GroceryList(Base):
    __tablename__ = "grocery_lists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_token = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GroceryItem(Base):
    __tablename__ = "grocery_items"
    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("grocery_lists.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    name = Column(String(255), nullable=False)
    quantity = Column(String(100), nullable=True)
    checked = Column(Integer, default=0, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
