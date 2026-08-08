import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "mysql+mysqlconnector://recipes:recipes@mysql:3306/recipes"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me")  # nosec B105 - runtime warning if default used
    MEDIA_ROOT: str = "/media"
    PUBLIC_URL: str = ""
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,*"

    @property
    def ALLOWED_ORIGINS_LIST(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def ALLOWED_HOSTS_LIST(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "ChangeMe123!"
    DEFAULT_ADMIN_DISPLAY_NAME: str = "Admin"

    DEFAULT_GUEST_EMAIL: str = "guest@whiskful.app"
    DEFAULT_GUEST_PASSWORD: str = "guest123!"
    DEFAULT_GUEST_DISPLAY_NAME: str = "Guest"
    GUEST_LOGIN_ENABLED: bool = True


settings = Settings()

# Warn if SECRET_KEY is not set (using insecure default)
if settings.SECRET_KEY == "change-me":  # nosec B105 - checking for default, not setting
    logging.warning(
        "WARNING: SECRET_KEY is not set (using default 'change-me'). "
        "This is insecure for production. Set the SECRET_KEY environment variable."
    )
