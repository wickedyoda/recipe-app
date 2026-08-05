from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

# Import all models BEFORE Base.metadata.create_all so SQLAlchemy registers them
from backend.config import settings
from backend.database import Base, SessionLocal, engine, ensure_schema
from backend.models import (
    Cookbook,
    GroceryItem,
    GroceryList,
    Note,
    Recipe,
    RecipeTag,
    Role,
    Store,
    Tag,
    User,
)  # noqa: F401 (registered with Base)
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


SEED_RECIPES = [
    {
        "title": "Spaghetti Aglio e Olio",
        "description": "Classic Italian pasta with garlic, olive oil, and red pepper flakes — simple, fast, and full of flavor.",
        "ingredients": "400g spaghetti\n4 cloves garlic, thinly sliced\n1/2 cup extra-virgin olive oil\n1/4 cup fresh parsley, chopped\n1/4 tsp red pepper flakes\nSalt to taste\n1/4 cup grated Parmesan cheese (optional)",
        "instructions": "1. Bring a large pot of salted water to a boil. Add spaghetti and cook until al dente, about 8-9 minutes.\n2. While pasta cooks, heat olive oil in a large pan over medium heat. Add garlic and red pepper flakes; cook until garlic is golden, about 2 minutes.\n3. Reserve 1/2 cup pasta water before draining. Add pasta to the pan with garlic oil.\n4. Toss with reserved pasta water, parsley, and Parmesan. Season with salt to taste.",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 4,
        "difficulty": "Easy",
        "category": "Pasta",
        "subcategory": "Italian",
        "flavor_rating": 4.5,
        "effort_rating": 2.0,
    },
    {
        "title": "Classic Chocolate Chip Cookies",
        "description": "Chewy, golden-brown cookies loaded with semi-sweet chocolate chips — perfect with a glass of milk.",
        "ingredients": "2 1/4 cups all-purpose flour\n1 tsp baking soda\n1 tsp salt\n1 cup unsalted butter, softened\n3/4 cup granulated sugar\n3/4 cup brown sugar\n2 large eggs\n2 tsp vanilla extract\n2 cups semi-sweet chocolate chips",
        "instructions": "1. Preheat oven to 375°F (190°C). Line baking sheets with parchment paper.\n2. In a bowl, whisk together flour, baking soda, and salt.\n3. In a separate bowl, cream butter, granulated sugar, and brown sugar until fluffy. Beat in eggs and vanilla.\n4. Gradually mix in the flour mixture until just combined. Stir in chocolate chips.\n5. Drop rounded tablespoons of dough onto baking sheets. Bake 9-11 minutes until golden brown.\n6. Let cool on baking sheet for 2 minutes, then transfer to wire rack.",
        "prep_time_minutes": 15,
        "cook_time_minutes": 10,
        "servings": 24,
        "difficulty": "Easy",
        "category": "Dessert",
        "subcategory": "Cookies",
        "flavor_rating": 5.0,
        "effort_rating": 2.5,
    },
    {
        "title": "Greek Salad",
        "description": "Fresh, vibrant salad with crisp vegetables, briny olives, and creamy feta cheese, dressed with olive oil and oregano.",
        "ingredients": "3 medium tomatoes, cut into wedges\n1 cucumber, sliced\n1/2 red onion, thinly sliced\n1/2 green bell pepper, sliced\n1/2 cup Kalamata olives\n8 oz feta cheese, cubed\n1/4 cup olive oil\n2 tbsp red wine vinegar\n1 tsp dried oregano\nSalt and pepper to taste",
        "instructions": "1. In a large bowl, combine tomatoes, cucumber, red onion, bell pepper, and olives.\n2. Add feta cheese cubes.\n3. In a small bowl, whisk together olive oil, red wine vinegar, oregano, salt, and pepper.\n4. Pour dressing over salad and toss gently.\n5. Let sit 10 minutes before serving for flavors to meld.",
        "prep_time_minutes": 15,
        "cook_time_minutes": 0,
        "servings": 4,
        "difficulty": "Easy",
        "category": "Salad",
        "subcategory": "Mediterranean",
        "flavor_rating": 4.0,
        "effort_rating": 1.5,
    },
]

SEED_TAGS = ["pasta", "italian", "dessert", "cookies", "salad", "mediterranean", "quick"]


def _bootstrap_guest_account() -> None:
    db = SessionLocal()
    try:
        guest_email = settings.DEFAULT_GUEST_EMAIL.strip().lower()
        existing = db.query(User).filter(func.lower(User.email) == guest_email).first()
        if existing:
            return

        guest = User(
            email=guest_email,
            hashed_password=hash_password(settings.DEFAULT_GUEST_PASSWORD),
            display_name=settings.DEFAULT_GUEST_DISPLAY_NAME,
            role=Role.user,
            is_active=1,
            is_approved=1,
            must_change_password=0,
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)

        cookbook = Cookbook(
            name="Sample Recipes",
            description="Starter recipes for the guest account",
            store=Store.local,
            owner_id=guest.id,
        )
        db.add(cookbook)
        db.commit()
        db.refresh(cookbook)

        tag_objs = {}
        for tag_name in SEED_TAGS:
            tag = db.query(Tag).filter(Tag.owner_id == guest.id, Tag.name == tag_name).first()
            if not tag:
                tag = Tag(owner_id=guest.id, name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            tag_objs[tag_name] = tag

        for seed in SEED_RECIPES:
            recipe = Recipe(
                title=seed["title"],
                description=seed["description"],
                ingredients=seed["ingredients"],
                instructions=seed["instructions"],
                store=Store.local,
                owner_id=guest.id,
                cookbook_id=cookbook.id,
                rating=seed.get("flavor_rating"),
                flavor_rating=seed.get("flavor_rating"),
                effort_rating=seed.get("effort_rating"),
                prep_time_minutes=seed["prep_time_minutes"],
                cook_time_minutes=seed["cook_time_minutes"],
                servings=seed["servings"],
                difficulty=seed["difficulty"],
                category=seed["category"],
                subcategory=seed["subcategory"],
            )
            db.add(recipe)
            db.commit()
            db.refresh(recipe)

            for tag_name in SEED_TAGS:
                if tag_name in seed["title"].lower() or tag_name in (seed.get("category", "") + " " + seed.get("subcategory", "")).lower():
                    db.add(RecipeTag(recipe_id=recipe.id, tag_id=tag_objs[tag_name].id))

            grocery_list = GroceryList(name=f"{seed['title']} Ingredients", owner_id=guest.id)
            db.add(grocery_list)
            db.commit()
            db.refresh(grocery_list)

            for line in seed["ingredients"].splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped[0].isdigit() or stripped[0] == "½" or stripped[0] == "¼":
                    name_part = stripped
                    for prefix in ("1 ", "2 ", "3 ", "4 ", "½ ", "¼ ", "¾ ", "1/2 ", "1/4 "):
                        if stripped.startswith(prefix):
                            name_part = stripped[len(prefix):]
                            break
                    db.add(GroceryItem(list_id=grocery_list.id, recipe_id=recipe.id, name=name_part, owner_id=guest.id))

            db.add(Note(recipe_id=recipe.id, owner_id=guest.id, body=f"Pro tip: {seed['instructions'].splitlines()[0] if seed['instructions'] else 'Enjoy!'}"))

        db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
ensure_schema()
_bootstrap_default_admin()
_bootstrap_guest_account()

app = FastAPI(title="Recipe App API", version="0.1.0")
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS_LIST,
)
app.mount("/media/static", StaticFiles(directory="backend/media"), name="backend-media")


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
