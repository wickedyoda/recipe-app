from fastapi import APIRouter
from .auth import router as auth_router
from .media import router as media_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(media_router, prefix="/media", tags=["media"])
