from fastapi import APIRouter
from backend.routers import auth as auth_router
from backend.routers import media as media_router
from backend.routers import recipes as recipes_router
from backend.routers import tags as tags_router
from backend.routers import notes as notes_router
from backend.routers import mealplans as mealplans_router
from backend.routers import grocery as grocery_router

router = APIRouter()
router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
router.include_router(media_router.router, prefix="/media", tags=["media"])
router.include_router(recipes_router.router, prefix="/recipes", tags=["recipes"])
router.include_router(tags_router.router, prefix="/tags", tags=["tags"])
router.include_router(notes_router.router, prefix="/notes", tags=["notes"])
router.include_router(mealplans_router.router, prefix="/meal-plans", tags=["meal-plans"])
router.include_router(grocery_router.router, prefix="/grocery-lists", tags=["grocery-lists"])
