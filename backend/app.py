from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

from backend.config import settings
from backend.database import Base, SessionLocal, engine, ensure_schema
from backend.models import Role, User
from backend.routers import router as api_router
from backend.services.auth import hash_password


def _bootstrap_default_admin() -> None:
    db = SessionLocal()
    try:
        admin_email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()
        existing = db.query(User).filter(func.lower(User.email) == admin_email).first()
        if existing:
            return
        admin = User(
            email=admin_email,
            hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            display_name=settings.DEFAULT_ADMIN_DISPLAY_NAME,
            role=Role.admin,
            is_active=1,
            is_approved=1,
            must_change_password=1,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
ensure_schema()
_bootstrap_default_admin()

app = FastAPI(title="Recipe App API", version="0.1.0")
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://docker.tail99133.ts.net:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[host.strip() for host in settings.ALLOWED_HOSTS.split(",") if host.strip()],
)
app.mount("/media", StaticFiles(directory="backend/media"), name="backend-media")

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response

app.include_router(api_router)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
