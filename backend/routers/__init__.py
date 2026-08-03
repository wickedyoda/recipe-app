from fastapi import APIRouter
from backend.routers import auth as auth_router
from backend.routers import media as media_router

router = APIRouter()
router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
router.include_router(media_router.router, prefix="/media", tags=["media"])
