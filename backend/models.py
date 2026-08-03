from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
import enum
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Cookbook(Base):
    __tablename__ = "cookbooks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    store = Column(Enum(Store), default=Store.local, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
