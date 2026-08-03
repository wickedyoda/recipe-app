from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import get_db, engine, Base
from .models import Recipe, User, Cookbook
from .schemas import RecipeCreate, RecipeOut, CookbookCreate, CookbookOut
from .auth import get_current_user
from .indexer import index_recipe
from .storage import save_upload
from .config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recipe App API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/recipes", response_model=RecipeOut)
def create_recipe(
    recipe: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = Recipe(**recipe.model_dump(), owner_id=current_user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    index_recipe(obj)
    return obj

@app.post("/recipes/upload", response_model=RecipeOut)
def upload_recipe(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path = save_upload(file)
    obj = Recipe(title="Imported recipe", source_path=path, owner_id=current_user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    index_recipe(obj)
    return obj

@app.get("/recipes", response_model=list[RecipeOut])
def list_recipes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Recipe).filter(Recipe.owner_id == current_user.id).all()

@app.post("/cookbooks", response_model=CookbookOut)
def create_cookbook(
    payload: CookbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = Cookbook(**payload.model_dump(), owner_id=current_user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/cookbooks", response_model=list[CookbookOut])
def list_cookbooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Cookbook).filter(Cookbook.owner_id == current_user.id).all()
