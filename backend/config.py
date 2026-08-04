from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+mysqlconnector://recipes:recipes@mysql:3306/recipes"
    SECRET_KEY: str = "change-me"
    MEDIA_ROOT: str = "/media"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,backend,*.ts.net"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "ChangeMe123!"
    DEFAULT_ADMIN_DISPLAY_NAME: str = "Admin"


settings = Settings()
