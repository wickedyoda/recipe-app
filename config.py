from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./recipes.db"
    SECRET_KEY: str = "change-me"
    STORAGE_DIR: str = "/tmp/recipe-uploads"

settings = Settings()
