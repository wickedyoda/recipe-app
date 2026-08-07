#!/usr/bin/env python3
"""Seed demo guest account with sample recipes, tags, meal plan, and grocery lists.
Run: python3 backend/scripts/seed_demo.py
"""

import sys
import os
import secrets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Recipe, Tag, MealPlan, MealPlanItem, GroceryList, GroceryItem, PasswordHistory

import bcrypt

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./recipes.db')
DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://')

# Try to use backend's SessionLocal first, fall back to direct engine
try:
    from database import SessionLocal
except ImportError:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_demo_user(db):
    """Create or update the demo guest account."""
    user = db.query(User).filter(User.email == 'guest@cookierue.app').first()
    password_hash = hash_password('Demo123!')

    if user:
        user.hashed_password = password_hash
        user.is_active = True
        user.is_readonly = True
        print(f"Updated existing demo user: {user.email}")
    else:
        user = User(
            email='guest@cookierue.app',
            display_name='Guest Demo',
            username='guest',
            hashed_password=password_hash,
            is_active=True,
            is_readonly=True
        )
        db.add(user)
        db.flush()  # Get the ID without committing
        print(f"Created demo user: {user.email}")

    # Record password history
    ph = PasswordHistory(user_id=user.id, hashed_password=password_hash)
    db.add(ph)

    return user

def create_tag(db, user_id, name):
    tag = db.query(Tag).filter(Tag.user_id == user_id, Tag.name == name).first()
    if not tag:
        tag = Tag(name=name, user_id=user_id)
        db.add(tag)
        db.flush()
    return tag

def create_recipe(db, user_id, title, category, description, ingredients, instructions, prep_time=None, cook_time=None, servings=None, difficulty=None, tags=None, photo=None):
    recipe = Recipe(
        user_id=user_id,
        title=title,
        category=category,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        prep_time=prep_time,
        cook_time=cook_time,
        servings=servings,
        difficulty=difficulty,
        source_path=photo
    )
    db.add(recipe)
    db.flush()

    if tags:
        for tag_name in tags:
            tag = create_tag(db, user_id, tag_name)
            recipe.tags.append(tag)

    return recipe

def create_grocery_list(db, user_id, name, items):
    grocery_list = GroceryList(user_id=user_id, name=name, shared_token=secrets.token_hex(8))
    db.add(grocery_list)
    db.flush()

    for item_text in items:
        item = GroceryItem(list_id=grocery_list.id, text=item_text, checked=False)
        db.add(item)

    return grocery_list

def create_meal_plan(db, user_id, name, date, entries):
    meal_plan = MealPlan(user_id=user_id, name=name, date=date)
    db.add(meal_plan)
    db.flush()

    for meal_type, recipe_id in entries:
        item = MealPlanItem(meal_plan_id=meal_plan.id, meal_type=meal_type, recipe_id=recipe_id)
        db.add(item)

    return meal_plan

def main():
    db = SessionLocal()
    try:
        user = create_demo_user(db)
        user_id = user.id

        # --- Tags ---
        all_tags = [
            'Breakfast', 'Lunch', 'Dinner', 'Dessert',
            'Vegetarian', 'Vegan', 'Gluten-Free', 'Easy',
            'Quick', 'Comfort Food', 'Italian', 'Mexican'
        ]
        for tag_name in all_tags:
            create_tag(db, user_id, tag_name)

        # --- Recipes (7) ---
        r1 = create_recipe(
            db, user_id, 'Pancakes', 'Breakfast',
            'Fluffy buttermilk pancakes with real maple syrup.',
            '- 1 cup flour\n- 2 tbsp sugar\n- 2 tsp baking powder\n- 1/2 tsp salt\n- 1 egg\n- 1/2 cup milk\n- 2 tbsp butter (melted)\n\n1. Mix dry ingredients.\n2. Add wet ingredients.\n3. Cook on skillet until bubbles form.\n4. Serve with syrup.',
            'https://images.unsplash.com/photo-1565560411438-4b7c8e4e2b67',
            prep_time=10, cook_time=15, servings=4, difficulty='Easy',
            tags=['Breakfast', 'Easy', 'Comfort Food']
        )
        r2 = create_recipe(
            db, user_id, 'Caprese Salad', 'Appetizers',
            'Classic Italian Caprese with fresh mozzarella, tomatoes, and basil.',
            '- 2 large tomatoes, sliced\n- 8 oz fresh mozzarella, sliced\n- 1/4 cup fresh basil\n- 2 tbsp olive oil\n- Salt and pepper to taste\n\n1. Layer tomatoes and mozzarella on a plate.\n2. Drizzle with olive oil.\n3. Top with basil and season.',
            'https://images.unsplash.com/photo-15460649043-d0d5e8c0e891',
            prep_time=10, cook_time=0, servings=4, difficulty='Easy',
            tags=['Appetizers', 'Italian', 'Vegetarian']
        )
        r3 = create_recipe(
            db, user_id, 'Spaghetti Bolognese', 'Entrees',
            'Classic Italian pasta with rich meat sauce.',
            '- 8 oz spaghetti\n- 1 lb ground beef\n- 1 onion, diced\n- 3 cloves garlic, minced\n- 1 (28oz) can tomatoes\n- 2 tbsp tomato paste\n- Salt, pepper, oregano\n\n1. Cook pasta.\n2. Brown beef with onion and garlic.\n3. Add tomatoes, paste, and spices. Simmer 30 min.\n4. Serve over pasta.',
            'https://images.unsplash.com/photo-1612899183523-ec6ad3355072',
            prep_time=15, cook_time=45, servings=6, difficulty='Medium',
            tags=['Entrees', 'Italian', 'Comfort Food']
        )
        r4 = create_recipe(
            db, user_id, 'Greek Yogurt Bowl', 'Breakfast',
            'Creamy Greek yogurt with honey, nuts, and fresh fruit.',
            '- 1 cup Greek yogurt\n- 1 tbsp honey\n- 2 tbsp granola\n- 1/2 cup mixed berries\n- 1 tbsp chopped nuts\n\n1. Layer yogurt in a bowl.\n2. Top with honey, granola, berries, and nuts.',
            'https://images.unsplash.com/photo-1494320433180-688fe2b67558',
            prep_time=5, cook_time=0, servings=1, difficulty='Easy',
            tags=['Breakfast', 'Vegetarian', 'Gluten-Free']
        )
        r5 = create_recipe(
            db, user_id, 'Chocolate Chip Cookies', 'Desserts',
            'Classic chewy chocolate chip cookies straight from the oven.',
            '- 2 1/4 cups flour\n- 1 tsp baking soda\n- 1 tsp salt\n- 1 cup butter, softened\n- 3/4 cup sugar\n- 3/4 cup brown sugar\n- 2 eggs\n- 2 tsp vanilla\n- 2 cups chocolate chips\n\n1. Preheat oven to 375°F.\n2. Mix dry ingredients.\n3. Cream butter and sugars.\n4. Add eggs and vanilla. Mix in flour.\n5. Fold in chocolate chips.\n6. Bake 10-12 min.',
            'https://images.unsplash.com/photo-1565560411438-4b7c8e4e2b67',
            prep_time=15, cook_time=12, servings=24, difficulty='Easy',
            tags=['Desserts', 'Easy']
        )
        r6 = create_recipe(
            db, user_id, 'Avocado Toast', 'Lunch',
            'Simple avocado toast with chili flakes and lemon.',
            '- 2 slices sourdough bread\n- 1 ripe avocado\n- 1 tbsp olive oil\n- 1/2 lemon\n- Chili flakes\n- Salt and pepper\n\n1. Toast bread.\n2. Mash avocado with lemon juice.\n3. Spread on toast.\n4. Drizzle with olive oil, season.',
            'https://images.unsplash.com/photo-1581291549493-3ecd0cc0fd37',
            prep_time=5, cook_time=5, servings=2, difficulty='Easy',
            tags=['Lunch', 'Vegetarian', 'Quick']
        )
        r7 = create_recipe(
            db, user_id, 'Beef Stir Fry', 'Entrees',
            'Quick beef stir fry with vegetables and soy sauce.',
            '- 1 lb beef, thinly sliced\n- 2 cups mixed vegetables\n- 3 cloves garlic, minced\n- 2 tbsp soy sauce\n- 1 tbsp oil\n- 1 tsp ginger\n\n1. Heat oil in pan.\n2. Cook beef until browned.\n3. Add vegetables and stir-fry 5 min.\n4. Add garlic, ginger, soy sauce. Cook 2 min.',
            'https://images.unsplash.com/photo-1588846022559-2192675c0587',
            prep_time=15, cook_time=10, servings=4, difficulty='Medium',
            tags=['Entrees', 'Quick', 'Comfort Food']
        )

        # --- Grocery Lists (2 lists, 5 items each) ---
        create_grocery_list(db, user_id, 'Weekly Shopping', [
            'Milk', 'Eggs', 'Bread', 'Tomatoes', 'Chicken breasts'
        ])
        create_grocery_list(db, user_id, 'Dessert Night', [
            'Chocolate chips', 'Flour', 'Butter', 'Brown sugar', 'Vanilla extract'
        ])

        # --- Meal Plan (1 plan, 2 entries) ---
        from datetime import date
        create_meal_plan(db, user_id, 'This Week', date.today(), [
            ('breakfast', r1.id),
            ('dinner', r3.id),
        ])

        db.commit()
        print(f"\n✅ Seeded demo guest account: guest@cookierue.app / Demo123!")
        print(f"   - 7 recipes")
        print(f"   - 16 tags")
        print(f"   - 2 grocery lists (5 items each)")
        print(f"   - 1 meal plan (2 entries)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()
