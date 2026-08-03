import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+mysqlconnector://recipes:recipes@mysql:3306/recipes"
    SECRET_KEY: str = "change-me"
    MEDIA_ROOT: str = "/media"

settings = Settings()
