import jwt as _jwt
from fastapi import FastAPI, JSONResponse, Request
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
    RecipeMedia,  # noqa: F401
    RecipeTag,
    Role,
    Store,
    Tag,
    User,
)  # noqa: F401 (registered with Base)
from backend.routers import router as api_router
from backend.services.auth import ALGORITHM, SECRET_KEY, hash_password


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
        "prep_time_minutes": 10, "cook_time_minutes": 15, "servings": 4,
        "difficulty": "Easy", "category": "Pasta", "subcategory": "Italian", "flavor_rating": 4.5, "effort_rating": 2.0,
    },
    {
        "title": "Classic Chocolate Chip Cookies",
        "description": "Chewy, golden-brown cookies loaded with semi-sweet chocolate chips — perfect with a glass of milk.",
        "ingredients": "2 1/4 cups all-purpose flour\n1 tsp baking soda\n1 tsp salt\n1 cup unsalted butter, softened\n3/4 cup granulated sugar\n3/4 cup brown sugar\n2 large eggs\n2 tsp vanilla extract\n2 cups semi-sweet chocolate chips",
        "instructions": "1. Preheat oven to 375°F (190°C). Line baking sheets with parchment paper.\n2. In a bowl, whisk together flour, baking soda, and salt.\n3. In a separate bowl, cream butter, granulated sugar, and brown sugar until fluffy. Beat in eggs and vanilla.\n4. Gradually mix in the flour mixture until just combined. Stir in chocolate chips.\n5. Drop rounded tablespoons of dough onto baking sheets. Bake 9-11 minutes until golden brown.\n6. Let cool on baking sheet for 2 minutes, then transfer to wire rack.",
        "prep_time_minutes": 15, "cook_time_minutes": 10, "servings": 24,
        "difficulty": "Easy", "category": "Dessert", "subcategory": "Cookies", "flavor_rating": 5.0, "effort_rating": 2.5,
    },
    {
        "title": "Greek Salad",
        "description": "Fresh, vibrant salad with crisp vegetables, briny olives, and creamy feta cheese, dressed with olive oil and oregano.",
        "ingredients": "3 medium tomatoes, cut into wedges\n1 cucumber, sliced\n1/2 red onion, thinly sliced\n1/2 green bell pepper, sliced\n1/2 cup Kalamata olives\n8 oz feta cheese, cubed\n1/4 cup olive oil\n2 tbsp red wine vinegar\n1 tsp dried oregano\nSalt and pepper to taste",
        "instructions": "1. In a large bowl, combine tomatoes, cucumber, red onion, bell pepper, and olives.\n2. Add feta cheese cubes.\n3. In a small bowl, whisk together olive oil, red wine vinegar, oregano, salt, and pepper.\n4. Pour dressing over salad and toss gently.\n5. Let sit 10 minutes before serving for flavors to meld.",
        "prep_time_minutes": 15, "cook_time_minutes": 0, "servings": 4,
        "difficulty": "Easy", "category": "Salad", "subcategory": "Mediterranean", "flavor_rating": 4.0, "effort_rating": 1.5,
    },
    {
        "title": "Beef Stir Fry",
        "description": "Tender beef with crisp vegetables in a savory soy-based sauce, served over rice.",
        "ingredients": "1 lb flank steak, thinly sliced\n2 tbsp vegetable oil\n3 cups mixed vegetables (bell peppers, broccoli, snap peas)\n3 cloves garlic, minced\n1 tbsp ginger, grated\n1/4 cup soy sauce\n2 tbsp oyster sauce\n1 tbsp brown sugar\n2 tsp sesame oil\n3 cups cooked rice",
        "instructions": "1. Heat oil in a wok or large skillet over high heat. Add beef and stir-fry 2-3 min until browned. Remove.\n2. Add more oil if needed. Stir-fry vegetables 3-4 min until crisp-tender.\n3. Add garlic and ginger; cook 30 seconds.\n4. Return beef to pan. Add soy sauce, oyster sauce, sugar, and sesame oil. Toss 2 min.\n5. Serve over rice.",
        "prep_time_minutes": 15, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Medium", "category": "Asian", "subcategory": "Stir Fry", "flavor_rating": 4.5, "effort_rating": 2.0,
    },
    {
        "title": "Margherita Pizza",
        "description": "Classic Neapolitan pizza with fresh mozzarella, tomato sauce, and basil on a crispy crust.",
        "ingredients": "1 pizza dough (store-bought or homemade)\n1/2 cup pizza sauce\n8 oz fresh mozzarella, sliced\n4-5 fresh basil leaves\n2 tbsp grated Parmesan\n1 tbsp olive oil\nSalt to taste",
        "instructions": "1. Preheat oven to 475°F (245°C).\n2. Roll out dough on a floured surface. Transfer to a pizza stone or baking sheet.\n3. Spread sauce over dough, leaving 1-inch border.\n4. Top with mozzarella and Parmesan.\n5. Bake 12-15 min until crust is golden and cheese is bubbly.\n6. Top with fresh basil and drizzle with olive oil.",
        "prep_time_minutes": 15, "cook_time_minutes": 15, "servings": 4,
        "difficulty": "Medium", "category": "Italian", "subcategory": "Pizza", "flavor_rating": 4.5, "effort_rating": 3.0,
    },
    {
        "title": "Chicken Tikka Masala",
        "description": "Tender chicken in a creamy, spiced tomato sauce with aromatic Indian flavors.",
        "ingredients": "1 lb boneless chicken thighs, cubed\n1 cup plain yogurt\n1 tbsp garam masala\n1 tsp ground cumin\n1 tsp paprika\n2 tbsp butter\n1 onion, diced\n3 cloves garlic, minced\n1 tbsp ginger, grated\n1 can (14oz) tomato sauce\n1 cup heavy cream\n1/2 tsp salt\nCilantro for garnish\nRice for serving",
        "instructions": "1. Marinate chicken with yogurt, garam masala, cumin, and paprika for 30 min.\n2. In a large pan, brown chicken in batches. Remove.\n3. Sauté onion, garlic, and ginger in butter until soft.\n4. Add tomato sauce and simmer 10 min.\n5. Return chicken, add cream and salt. Simmer 10 min.\n6. Garnish with cilantro. Serve with rice.",
        "prep_time_minutes": 30, "cook_time_minutes": 25, "servings": 4,
        "difficulty": "Medium", "category": "Indian", "subcategory": "Curry", "flavor_rating": 5.0, "effort_rating": 3.0,
    },
    {
        "title": "Caesar Salad",
        "description": "Crisp romaine lettuce with parmesan, croutons, and a creamy homemade Caesar dressing.",
        "ingredients": "2 heads romaine lettuce, chopped\n1/2 cup grated Parmesan\n1 cup croutons\n1/4 cup Caesar dressing\n1/4 cup olive oil\n2 cloves garlic, minced\n1 anchovy paste (optional)\n1 egg yolk\n1 tbsp lemon juice\nSalt and pepper to taste",
        "instructions": "1. Make dressing: whisk egg yolk, lemon juice, garlic, and anchovy paste. Slowly add oil and Parmesan.\n2. Toss romaine with dressing.\n3. Top with croutons and remaining Parmesan.\n4. Season with salt and pepper.",
        "prep_time_minutes": 15, "cook_time_minutes": 0, "servings": 4,
        "difficulty": "Easy", "category": "Salad", "subcategory": "American", "flavor_rating": 3.5, "effort_rating": 2.0,
    },
    {
        "title": "Avocado Toast",
        "description": "Simple, healthy breakfast with mashed avocado on toasted sourdough with lemon and chili.",
        "ingredients": "2 slices sourdough bread\n1 ripe avocado\n1 tbsp lemon juice\nPinch red pepper flakes\nSalt and pepper to taste\n1/2 tsp olive oil (optional)\nMicrogreens for garnish (optional)",
        "instructions": "1. Toast bread to desired crispness.\n2. In a bowl, mash avocado with lemon juice, salt, and pepper.\n3. Spread on toast.\n4. Drizzle with olive oil if desired.\n5. Sprinkle with red pepper flakes and garnish with microgreens.",
        "prep_time_minutes": 5, "cook_time_minutes": 5, "servings": 2,
        "difficulty": "Easy", "category": "Breakfast", "subcategory": "Quick", "flavor_rating": 4.0, "effort_rating": 1.0,
    },
    {
        "title": "Bolognese Pasta",
        "description": "Rich, slow-cooked meat sauce served with al dente pasta — comfort food at its finest.",
        "ingredients": "12 oz pappardelle or tagliatelle\n1 lb ground beef\n1 onion, finely diced\n2 carrots, finely diced\n2 celery stalks, finely diced\n4 cloves garlic, minced\n1 can (28oz) crushed tomatoes\n1/2 cup red wine\n2 tbsp tomato paste\n1 tsp dried oregano\n1/2 cup heavy cream\n1/2 cup grated Parmesan\nSalt and pepper to taste\nFresh basil for garnish",
        "instructions": "1. Cook pasta according to package directions. Reserve 1/2 cup pasta water.\n2. In a large pot, brown beef. Add onion, carrots, celery; cook 5 min.\n3. Add garlic, tomato paste; cook 1 min.\n4. Pour in wine; simmer until reduced by half.\n5. Add tomatoes, oregano, salt, and pepper. Simmer 30 min.\n6. Stir in cream and pasta water. Serve over pasta with Parmesan and basil.",
        "prep_time_minutes": 20, "cook_time_minutes": 45, "servings": 6,
        "difficulty": "Hard", "category": "Pasta", "subcategory": "Italian", "flavor_rating": 4.8, "effort_rating": 4.0,
    },
    {
        "title": "Chicken Buddha Bowl",
        "description": "Nutritious bowl with grilled chicken, quinoa, roasted vegetables, and tahini dressing.",
        "ingredients": "1 cup quinoa, rinsed\n1 lb chicken breast, cubed\n2 tbsp olive oil\n1 sweet potato, cubed\n1 cup broccoli florets\n1 cup chickpeas, drained\n1 avocado, sliced\n2 tbsp tahini\n1 tbsp lemon juice\n1 tsp maple syrup\nSalt and pepper to taste",
        "instructions": "1. Cook quinoa in 2 cups water. Simmer 15 min until water absorbed.\n2. Toss sweet potato with 1 tbsp oil and roast 25 min at 400°F.\n3. Season chicken with salt and pepper. Sear in remaining oil 6-8 min per side.\n4. Steam broccoli 5 min. Drain chickpeas.\n5. Whisk tahini, lemon juice, maple syrup, and water to thin.\n6. Assemble bowls: quinoa, chicken, sweet potato, broccoli, chickpeas, avocado. Drizzle with tahini.",
        "prep_time_minutes": 20, "cook_time_minutes": 30, "servings": 4,
        "difficulty": "Medium", "category": "Healthy", "subcategory": "Bowl", "flavor_rating": 4.2, "effort_rating": 3.0,
    },
    {
        "title": "Carbonara",
        "description": "Classic Roman pasta with pancetta, egg, and pecorino cheese — creamy without cream.",
        "ingredients": "8 oz spaghetti\n3 egg yolks\n1/2 cup grated Pecorino Romano\n2 oz pancetta or guanciale, diced\n2 cloves garlic, minced\n1/2 cup reserved pasta water\nFreshly ground black pepper\nSalt to taste",
        "instructions": "1. Cook spaghetti until al dente. Reserve 1/2 cup pasta water.\n2. Meanwhile, whisk egg yolks with Pecorino. Season with plenty of black pepper.\n3. Cook pancetta in a large pan until crispy. Add garlic for 30 seconds.\n4. Toss hot pasta with pancetta. Remove from heat.\n5. Quickly stir in egg mixture and pasta water until creamy.\n6. Serve immediately with extra cheese and pepper.",
        "prep_time_minutes": 10, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Medium", "category": "Pasta", "subcategory": "Italian", "flavor_rating": 4.5, "effort_rating": 2.0,
    },
    {
        "title": "Fish Tacos",
        "description": "Crispy battered fish in warm tortillas with cabbage slaw and lime crema.",
        "ingredients": "1 lb white fish (cod or halibut), cut into strips\n1 cup flour\n1/2 cup cornstarch\n1 tsp baking powder\n1/2 tsp salt\n1 egg\n3/4 cup beer (or water)\n1/2 head green cabbage, shredded\n1/4 cup mayo\n1 tbsp lime juice\n1 tsp honey\n8 small corn tortillas\nLime wedges for serving\nCilantro for garnish",
        "instructions": "1. Whisk flour, cornstarch, baking powder, and salt. Add egg and beer; mix to batter.\n2. Heat oil in a deep pan. Dip fish in batter; fry 3-4 min until golden.\n3. Mix cabbage, mayo, lime juice, honey, and salt for slaw.\n4. Warm tortillas. Fill with fish and slaw.\n5. Serve with lime and cilantro.",
        "prep_time_minutes": 15, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Medium", "category": "Mexican", "subcategory": "Tacos", "flavor_rating": 4.3, "effort_rating": 3.0,
    },
    {
        "title": "Beef Burger",
        "description": "Juicy, flame-grilled beef burger with all the fixings on a toasted brioche bun.",
        "ingredients": "1 lb ground beef (80/20)\n4 brioche buns\n4 leaves lettuce\n4 slices tomato\n4 slices red onion\n4 slices cheddar cheese (optional)\n2 tbsp mayonnaise\n1 tbsp ketchup\n1 tsp Dijon mustard\n1 tsp Worcestershire sauce\nSalt and pepper to taste\nButter for toasting buns",
        "instructions": "1. Mix mayo, ketchup, mustard, Worcestershire, salt, and pepper.\n2. Form beef into 4 patties. Season with salt and pepper.\n3. Grill patties 4-5 min per side (or to desired doneness). Add cheese last min.\n4. Toast buns with butter.\n5. Spread mayo on buns. Add lettuce, tomato, onion, and patty. Serve hot.",
        "prep_time_minutes": 10, "cook_time_minutes": 12, "servings": 4,
        "difficulty": "Easy", "category": "American", "subcategory": "Burgers", "flavor_rating": 4.2, "effort_rating": 1.5,
    },
    {
        "title": "Vegetable Curry",
        "description": "A rich, aromatic curry bursting with colorful vegetables in a creamy coconut sauce.",
        "ingredients": "1 can (14oz) coconut milk\n2 tbsp curry powder\n1 onion, diced\n3 cloves garlic, minced\n1 tbsp ginger, grated\n1 sweet potato, cubed\n1 cup cauliflower florets\n1 cup bell peppers, mixed colors\n1/2 cup green beans\n1 cup spinach\n1 tbsp tomato paste\n1 tsp turmeric\nSalt to taste\nRice for serving",
        "instructions": "1. Sauté onion, garlic, and ginger in a pot until soft.\n2. Stir in curry powder, turmeric, and tomato paste; cook 1 min.\n3. Add coconut milk, sweet potato, cauliflower, bell peppers, and green beans.\n4. Simmer 20 min until vegetables are tender.\n5. Stir in spinach until wilted. Season with salt.\n6. Serve over rice.",
        "prep_time_minutes": 15, "cook_time_minutes": 25, "servings": 4,
        "difficulty": "Easy", "category": "Indian", "subcategory": "Curry", "flavor_rating": 4.0, "effort_rating": 1.5,
    },
    {
        "title": "Pancakes",
        "description": "Fluffy buttermilk pancakes topped with maple syrup and fresh berries — the perfect breakfast.",
        "ingredients": "1 1/2 cups flour\n3 1/2 tsp baking powder\n1 tsp salt\n1 cup white sugar\n1 1/4 cups buttermilk\n1 egg\n1/3 cup melted butter\n1 tsp vanilla extract\nMaple syrup and berries for topping",
        "instructions": "1. Whisk flour, baking powder, salt, and sugar.\n2. In another bowl, beat buttermilk, egg, melted butter, and vanilla.\n3. Combine wet and dry ingredients; stir until just mixed.\n4. Heat a griddle. Pour 1/4 cup batter per pancake.\n5. Cook 2-3 min until bubbles form. Flip; cook 1-2 min more.\n6. Serve with maple syrup and berries.",
        "prep_time_minutes": 10, "cook_time_minutes": 15, "servings": 4,
        "difficulty": "Easy", "category": "Breakfast", "subcategory": "Pancakes", "flavor_rating": 4.5, "effort_rating": 1.0,
    },
    {
        "title": "Clam Chowder",
        "description": "Creamy New England clam chowder with tender clams, potatoes, and bacon in a rich broth.",
        "ingredients": "4 cups clam juice\n2 cans (6oz each) chopped clams\n4 slices bacon, diced\n2 potatoes, diced\n1 onion, diced\n2 carrots, diced\n2 celery stalks, diced\n3 cloves garlic, minced\n3 tbsp flour\n1 cup heavy cream\n1 tsp thyme\nSalt and pepper to taste",
        "instructions": "1. Cook bacon in a pot until crispy. Remove; reserve drippings.\n2. Sauté onion, carrots, celery in drippings 5 min. Add garlic; cook 1 min.\n3. Stir in flour; cook 2 min.\n4. Gradually whisk in clam juice. Add potatoes and thyme.\n5. Simmer 15 min until potatoes are tender.\n6. Add clams and cream. Heat through (don't boil). Season and serve.",
        "prep_time_minutes": 15, "cook_time_minutes": 25, "servings": 6,
        "difficulty": "Hard", "category": "Soup", "subcategory": "Chowder", "flavor_rating": 4.7, "effort_rating": 3.5,
    },
    {
        "title": "Pad Thai",
        "description": "Stir-fried rice noodles with eggs, shrimp, bean sprouts, and peanuts in a tangy tamarind sauce.",
        "ingredients": "8 oz rice noodles\n2 tbsp vegetable oil\n2 eggs, scrambled\n2 cloves garlic, minced\n1/2 cup firm tofu, cubed\n1/2 cup bean sprouts\n2 green onions, chopped\n1/4 cup crushed peanuts\n1 tbsp tamarind paste\n1 tbsp fish sauce\n1 tbsp sugar\n1 tbsp lime juice\n1/4 cup cilantro for garnish\n1 lime, cut into wedges",
        "instructions": "1. Soak rice noodles in hot water 8 min until soft. Drain.\n2. Heat oil in a wok. Scramble eggs; remove.\n3. Stir-fry garlic and tofu 2 min.\n4. Add noodles, tamarind, fish sauce, sugar, and lime juice. Toss 2 min.\n5. Add eggs back. Top with bean sprouts, green onions, peanuts, and cilantro.\n6. Serve with lime wedges.",
        "prep_time_minutes": 15, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Medium", "category": "Asian", "subcategory": "Thai", "flavor_rating": 4.8, "effort_rating": 2.5,
    },
    {
        "title": "Roast Chicken",
        "description": "A classic roast chicken with crispy golden skin and juicy, flavorful meat — perfect comfort food.",
        "ingredients": "1 whole chicken (4 lbs)\n2 tbsp olive oil\n1 lemon, halved\n4 cloves garlic, smashed\n4 sprigs rosemary\n4 sprigs thyme\n1 onion, quartered\n3 carrots, chopped\n2 celery stalks, chopped\nSalt and pepper to taste",
        "instructions": "1. Preheat oven to 425°F (220°C).\n2. Pat chicken dry. Rub with olive oil, salt, and pepper inside and out.\n3. Stuff cavity with lemon, garlic, and herbs.\n4. Place on a bed of onion, carrots, and celery in a roasting pan.\n5. Roast 1.5-2 hours until internal temp reaches 165°F.\n6. Let rest 15 min before carving.",
        "prep_time_minutes": 15, "cook_time_minutes": 105, "servings": 6,
        "difficulty": "Hard", "category": "American", "subcategory": "Roast", "flavor_rating": 4.6, "effort_rating": 1.5,
    },
    {
        "title": "Caprese Salad",
        "description": "Simple Italian salad with fresh mozzarella, tomatoes, basil, and a drizzle of balsamic glaze.",
        "ingredients": "3 ripe tomatoes, sliced\n8 oz fresh mozzarella, sliced\n1/4 cup fresh basil leaves\n2 tbsp olive oil\n1 tbsp balsamic vinegar\nSalt and pepper to taste\nBalsamic glaze for drizzling",
        "instructions": "1. Arrange tomato and mozzarella slices on a plate, alternating.\n2. Tuck basil leaves between slices.\n3. Drizzle with olive oil and balsamic vinegar.\n4. Season with salt and pepper.\n5. Drizzle with balsamic glaze before serving.",
        "prep_time_minutes": 10, "cook_time_minutes": 0, "servings": 4,
        "difficulty": "Easy", "category": "Salad", "subcategory": "Italian", "flavor_rating": 4.0, "effort_rating": 1.0,
    },
    {
        "title": "Shrimp Scampi",
        "description": "Garlicky shrimp sautéed in butter and white wine, served over linguine.",
        "ingredients": "8 oz linguine\n1 lb large shrimp, peeled and deveined\n4 cloves garlic, thinly sliced\n1/2 cup dry white wine\n1/4 cup butter\n1/4 cup fresh parsley, chopped\n1 tbsp lemon juice\n1/2 tsp red pepper flakes\nSalt to taste\n1/4 cup grated Parmesan (optional)",
        "instructions": "1. Cook linguine; reserve 1/2 cup pasta water.\n2. Melt butter in a large pan over medium-high heat.\n3. Add garlic; cook 30 seconds.\n4. Add shrimp; cook 2 min per side until pink.\n5. Pour in wine; reduce 2 min.\n6. Add pasta water, parsley, lemon juice, and pepper flakes. Toss with linguine.\n7. Top with Parmesan if desired.",
        "prep_time_minutes": 10, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Medium", "category": "Seafood", "subcategory": "Pasta", "flavor_rating": 4.5, "effort_rating": 1.5,
    },
    {
        "title": "Tacos al Pastor",
        "description": "Authentic Mexican tacos with marinated pork, pineapple, and fresh cilantro on corn tortillas.",
        "ingredients": "1 lb pork shoulder, thinly sliced\n1/4 cup achiote paste\n1/2 cup pineapple juice\n2 cloves garlic, minced\n1 tsp dried oregano\n1/2 tsp cumin\n1/2 cup fresh pineapple, diced\n1/2 onion, finely diced\n1 jalapeño, minced\n1/4 cup cilantro, chopped\n12 corn tortillas\n2 limes, cut into wedges",
        "instructions": "1. Marinate pork with achiote, pineapple juice, garlic, oregano, and cumin for 2 hours.\n2. Grill or pan-sear pork until charred, about 5 min per side.\n3. Warm tortillas. Fill with pork, pineapple, onion, jalapeño, and cilantro.\n4. Serve with lime wedges.",
        "prep_time_minutes": 20, "cook_time_minutes": 15, "servings": 4,
        "difficulty": "Medium", "category": "Mexican", "subcategory": "Tacos", "flavor_rating": 4.7, "effort_rating": 3.0,
    },
    {
        "title": "Mac and Cheese",
        "description": "Creamy, cheesy elbow pasta baked with a golden, crispy crust — pure comfort food.",
        "ingredients": "1 lb elbow macaroni\n4 tbsp butter\n4 tbsp flour\n2 cups milk\n2 cups shredded sharp cheddar\n1/2 cup grated Parmesan\n1/2 tsp mustard powder\n1/4 tsp paprika\n1 cup panko breadcrumbs\nSalt and pepper to taste",
        "instructions": "1. Preheat oven to 375°F (190°C). Cook macaroni; drain.\n2. In a saucepan, melt butter. Whisk in flour; cook 2 min.\n3. Gradually whisk in milk; simmer until thick, 5 min.\n4. Remove from heat. Stir in cheddar, Parmesan, mustard, paprika, salt, and pepper.\n5. Mix with pasta. Top with breadcrumbs.\n6. Bake 25 min until bubbly and golden.",
        "prep_time_minutes": 15, "cook_time_minutes": 25, "servings": 6,
        "difficulty": "Easy", "category": "American", "subcategory": "Pasta", "flavor_rating": 4.3, "effort_rating": 2.0,
    },
    {
        "title": "Sushi Rolls",
        "description": "Homemade maki rolls with short-grain rice, nori, fresh vegetables, and optional crab or avocado.",
        "ingredients": "2 cups sushi rice\n2 cups water\n1/4 cup rice vinegar\n2 tbsp sugar\n1 tsp salt\n4 nori sheets\n1 avocado, sliced\n1 cucumber, julienned\n4 oz crab or imitation crab\n1 carrot, julienned\nSoy sauce and wasabi for serving",
        "instructions": "1. Rinse rice. Cook with water 18 min. Let stand 10 min.\n2. Mix rice vinegar, sugar, and salt. Fold into rice.\n3. Place nori on a bamboo mat. Spread rice over 3/4 of sheet.\n4. Add fillings at the bottom edge.\n5. Roll tightly using the mat. Slice into 6-8 pieces.\n6. Serve with soy sauce and wasabi.",
        "prep_time_minutes": 30, "cook_time_minutes": 25, "servings": 4,
        "difficulty": "Hard", "category": "Japanese", "subcategory": "Sushi", "flavor_rating": 4.6, "effort_rating": 4.0,
    },
    {
        "title": "Banana Bread",
        "description": "Moist, flavorful banana bread with a golden crust — perfect for breakfast or a snack.",
        "ingredients": "3 ripe bananas, mashed\n1/3 cup melted butter\n3/4 cup sugar\n1 egg, beaten\n1 tsp vanilla extract\n1 tsp baking soda\nPinch salt\n1 1/2 cups flour",
        "instructions": "1. Preheat oven to 350°F (175°C). Grease a loaf pan.\n2. Mix bananas and melted butter.\n3. Stir in sugar, egg, and vanilla. Sprinkle baking soda over; stir.\n4. Add salt and flour; fold until just combined.\n5. Pour into loaf pan. Bake 60-65 min until a toothpick comes out clean.\n6. Cool 10 min before slicing.",
        "prep_time_minutes": 10, "cook_time_minutes": 65, "servings": 8,
        "difficulty": "Easy", "category": "Dessert", "subcategory": "Bread", "flavor_rating": 4.2, "effort_rating": 1.0,
    },
    {
        "title": "Pho",
        "description": "Fragrant Vietnamese noodle soup with tender beef, rice noodles, and fresh herbs in rich broth.",
        "ingredients": "4 cups beef broth\n1 lb beef sirloin, thinly sliced\n1 cup rice noodles\n2 tbsp pho spice\n3 cloves garlic, minced\n1 onion, halved\n1 star anise\n1 cinnamon stick\n1/4 cup fish sauce\n1 tbsp sugar\n1 lime, cut into wedges\n1/4 cup cilantro\n1/4 cup Thai basil\n1 jalapeño, sliced\nBean sprouts",
        "instructions": "1. Char onion and garlic. Add to broth with spices, fish sauce, and sugar.\n2. Simmer 30 min. Strain.\n3. Soak rice noodles in hot water 5 min. Drain.\n4. Thinly slice raw beef.\n5. Assemble bowls: noodles, raw beef, herbs. Pour hot broth over (it cooks the beef).\n6. Add lime, bean sprouts, and jalapeño.",
        "prep_time_minutes": 20, "cook_time_minutes": 35, "servings": 4,
        "difficulty": "Hard", "category": "Asian", "subcategory": "Soup", "flavor_rating": 4.8, "effort_rating": 2.5,
    },
    {
        "title": "BLT Sandwich",
        "description": "Classic American sandwich with crispy bacon, fresh lettuce, tomato, and mayo on toasted bread.",
        "ingredients": "8 slices bacon\n8 slices bread\n4 leaves lettuce\n1 large tomato, sliced\n4 tbsp mayonnaise\n1 tbsp mustard (optional)\nSalt and pepper to taste",
        "instructions": "1. Cook bacon until crispy. Drain on paper towels.\n2. Toast bread. Spread mayo (and mustard if using) on one side of each slice.\n3. Layer lettuce, tomato, and bacon on 4 slices.\n4. Season tomato with salt and pepper.\n5. Top with remaining bread. Serve immediately.",
        "prep_time_minutes": 10, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Easy", "category": "American", "subcategory": "Sandwich", "flavor_rating": 3.8, "effort_rating": 0.5,
    },
    {
        "title": "Mushroom Risotto",
        "description": "Creamy Arborio rice cooked with mushrooms, white wine, and Parmesan — rich and comforting.",
        "ingredients": "1 cup Arborio rice\n4 cups chicken or vegetable broth\n1/2 cup dry white wine\n8 oz mushrooms, sliced\n1 onion, diced\n2 cloves garlic, minced\n1/2 cup grated Parmesan\n2 tbsp butter\n2 tbsp olive oil\n1/4 cup fresh parsley, chopped\nSalt and pepper to taste",
        "instructions": "1. Heat broth in a saucepan; keep warm.\n2. Sauté onion in oil until soft. Add mushrooms; cook until golden.\n3. Add garlic and rice; cook 2 min until rice is toasted.\n4. Pour in wine; stir until absorbed.\n5. Add broth 1/2 cup at a time, stirring until absorbed.\n6. Stir in butter, Parmesan, and parsley. Season to taste.",
        "prep_time_minutes": 15, "cook_time_minutes": 30, "servings": 4,
        "difficulty": "Hard", "category": "Italian", "subcategory": "Risotto", "flavor_rating": 4.5, "effort_rating": 3.5,
    },
    {
        "title": "Guacamole",
        "description": "Fresh, chunky guacamole with ripe avocados, lime, cilantro, and a hint of jalapeño heat.",
        "ingredients": "3 ripe avocados\n1 lime, juiced\n1/2 red onion, finely diced\n1 jalapeño, seeded and minced\n1/4 cup fresh cilantro, chopped\n1 tomato, diced\n1 clove garlic, minced\nSalt to taste",
        "instructions": "1. Cut avocados in half and remove pits.\n2. Scoop flesh into a bowl. Mash with a fork to desired consistency.\n3. Add lime juice immediately to prevent browning.\n4. Stir in onion, jalapeño, cilantro, tomato, and garlic.\n5. Season with salt to taste.\n6. Let sit 10 min before serving. Serve with tortilla chips.",
        "prep_time_minutes": 10, "cook_time_minutes": 0, "servings": 6,
        "difficulty": "Easy", "category": "Dip", "subcategory": "Mexican", "flavor_rating": 4.5, "effort_rating": 0.5,
    },
    {
        "title": "Beef Ramen",
        "description": "Rich tonkotsu-style ramen with tender beef, curly noodles, and a perfectly soft-boiled egg.",
        "ingredients": "4 cups beef broth\n2 tbsp miso paste\n1 tbsp soy sauce\n1 tbsp mirin\n2 green onions, chopped\n2 soft-boiled eggs\n2 servings ramen noodles\n4 oz beef, thinly sliced\n1/2 cup bean sprouts\n1 tbsp nori strips\n1 tsp sesame oil",
        "instructions": "1. Heat broth with miso, soy sauce, and mirin.\n2. In a separate pot, cook ramen noodles according to package.\n3. Thinly slice raw beef paper-thin.\n4. Divide noodles between bowls. Top with bean sprouts.\n5. Pour hot broth over beef (it cooks it). Add halved soft-boiled eggs.\n6. Garnish with green onions, nori, and sesame oil.",
        "prep_time_minutes": 15, "cook_time_minutes": 20, "servings": 2,
        "difficulty": "Medium", "category": "Asian", "subcategory": "Ramen", "flavor_rating": 4.4, "effort_rating": 2.0,
    },
    {
        "title": "Key Lime Pie",
        "description": "Tart and creamy key lime pie with a graham cracker crust and fluffy meringue topping.",
        "ingredients": "1 graham cracker crust (9-inch)\n1 can (14oz) sweetened condensed milk\n1/2 cup key lime juice\n2 tsp lime zest\n3 egg yolks\n1/2 cup heavy cream\n2 tbsp sugar\n1/2 cup crushed graham crackers for garnish",
        "instructions": "1. Preheat oven to 350°F (175°C).\n2. Whisk condensed milk, lime juice, zest, and egg yolks until thick.\n3. Pour into crust. Bake 15 min until set.\n4. Cool completely. Refrigerate 2 hours.\n5. Whip cream with sugar until stiff peaks. Spread over pie.\n6. Garnish with crushed graham crackers.",
        "prep_time_minutes": 15, "cook_time_minutes": 15, "servings": 8,
        "difficulty": "Medium", "category": "Dessert", "subcategory": "Pie", "flavor_rating": 4.3, "effort_rating": 2.0,
    },
    {
        "title": "Lobster Roll",
        "description": "Buttery toasted roll filled with chilled lobster meat tossed in a light mayo and herb dressing.",
        "ingredients": "1 lb lobster meat, chopped\n2 tbsp mayonnaise\n1 tbsp lemon juice\n1 tbsp chopped chives\n1/4 tsp celery salt\n2 lobster rolls (or split-top buns)\n2 tbsp melted butter\nSalt and pepper to taste",
        "instructions": "1. Chop cooked lobster meat.\n2. Mix with mayo, lemon juice, chives, celery salt, salt, and pepper.\n3. Chill 30 min.\n4. Toast buns with melted butter.\n5. Fill with lobster mixture. Serve chilled.",
        "prep_time_minutes": 10, "cook_time_minutes": 5, "servings": 2,
        "difficulty": "Easy", "category": "Seafood", "subcategory": "Sandwich", "flavor_rating": 5.0, "effort_rating": 1.0,
    },
    {
        "title": "Chicken Caesar Wrap",
        "description": "Grilled chicken, romaine, parmesan, and Caesar dressing rolled up in a soft flour tortilla.",
        "ingredients": "1 boneless chicken breast\n1 tbsp olive oil\nSalt and pepper to taste\n1 large flour tortilla\n1/4 cup Caesar dressing\n1/4 cup grated Parmesan\n1/2 cup romaine lettuce, shredded\n1/4 cup croutons",
        "instructions": "1. Season chicken with salt and pepper. Grill in oil 6-7 min per side. Slice.\n2. Warm tortilla.\n3. Spread Caesar dressing on tortilla.\n4. Add chicken, lettuce, Parmesan, and croutons.\n5. Fold sides in and roll tightly. Slice and serve.",
        "prep_time_minutes": 10, "cook_time_minutes": 15, "servings": 2,
        "difficulty": "Easy", "category": "American", "subcategory": "Wrap", "flavor_rating": 4.0, "effort_rating": 1.5,
    },
    {
        "title": "Pad See You",
        "description": "Stir-fried wide rice noodles with eggs, shrimp, bean sprouts, and peanuts in a sweet-savory sauce.",
        "ingredients": "8 oz wide rice noodles\n2 tbsp oil\n2 eggs\n2 cloves garlic, minced\n1/2 cup firm tofu, cubed\n1/2 cup bean sprouts\n2 green onions\n2 tbsp soy sauce\n1 tbsp fish sauce\n1 tsp sugar\n1/4 cup crushed peanuts\nCilantro",
        "instructions": "1. Soak noodles in hot water 8 min. Drain.\n2. Heat oil. Scramble eggs; remove.\n3. Sauté garlic and tofu 2 min.\n4. Add noodles, soy sauce, fish sauce, sugar. Toss 2 min.\n5. Add eggs back. Top with bean sprouts, green onions, peanuts, cilantro.",
        "prep_time_minutes": 15, "cook_time_minutes": 10, "servings": 4,
        "difficulty": "Easy", "category": "Asian", "subcategory": "Thai", "flavor_rating": 4.3, "effort_rating": 1.5,
    },
    {
        "title": "Chana Masala",
        "description": "Spiced chickpea curry with tomatoes, onions, and warming Indian spices — fragrant and satisfying.",
        "ingredients": "2 cans (15oz) chickpeas, drained\n1 onion, diced\n3 cloves garlic, minced\n1 tbsp ginger, grated\n1 can (14oz) diced tomatoes\n1 tsp cumin\n1 tsp coriander\n1/2 tsp turmeric\n1/2 tsp garam masala\n1/4 tsp cayenne\n1/2 cup water\n2 tbsp olive oil\nSalt to taste\nCilantro for garnish\nRice for serving",
        "instructions": "1. Heat oil in a pot. Sauté onion until soft, 5 min.\n2. Add garlic, ginger, and spices; cook 1 min.\n3. Add tomatoes and water. Simmer 10 min.\n4. Add chickpeas. Simmer 15 min.\n5. Stir in garam masala. Season with salt.\n6. Garnish with cilantro. Serve with rice.",
        "prep_time_minutes": 10, "cook_time_minutes": 25, "servings": 4,
        "difficulty": "Easy", "category": "Indian", "subcategory": "Curry", "flavor_rating": 4.4, "effort_rating": 1.0,
    },
    {
        "title": "Grilled Cheese",
        "description": "The ultimate comfort food sandwich — crispy buttered bread with melted, gooey cheese.",
        "ingredients": "2 slices sourdough bread\n2 oz sharp cheddar cheese, sliced\n1 oz Gruyère cheese, sliced\n2 tbsp butter, softened\n1/4 tsp garlic powder (optional)\nPinch of paprika",
        "instructions": "1. Butter one side of each bread slice.\n2. Layer cheeses between the unbuttered sides.\n3. Heat a skillet over medium heat.\n4. Cook sandwich buttered-side-down 3-4 min until golden.\n5. Flip; cook 3-4 min until other side is golden and cheese is melted.\n6. Sprinkle with paprika. Slice and serve.",
        "prep_time_minutes": 5, "cook_time_minutes": 10, "servings": 1,
        "difficulty": "Easy", "category": "American", "subcategory": "Sandwich", "flavor_rating": 4.0, "effort_rating": 0.5,
    },
    {
        "title": "Chicken Alfredo",
        "description": "Tender chicken and fettuccine pasta in a rich, creamy parmesan sauce with a hint of garlic.",
        "ingredients": "8 oz fettuccine\n1 lb chicken breast, cubed\n4 tbsp butter\n3 cloves garlic, minced\n1 cup heavy cream\n1/2 cup grated Parmesan\n1/4 tsp nutmeg\nSalt and pepper to taste\nFresh parsley for garnish",
        "instructions": "1. Cook fettuccine. Reserve 1/2 cup pasta water.\n2. Season chicken with salt and pepper. Sear in a pan until golden, about 5 min.\n3. Reduce heat. Add butter and garlic; cook 30 sec.\n4. Pour in cream; simmer 2 min.\n5. Stir in Parmesan until melted. Add pasta water if too thick.\n6. Toss with pasta. Garnish with parsley.",
        "prep_time_minutes": 10, "cook_time_minutes": 15, "servings": 4,
        "difficulty": "Easy", "category": "Pasta", "subcategory": "Italian", "flavor_rating": 4.3, "effort_rating": 1.5,
    },
]

SEED_TAGS = ["pasta", "italian", "dessert", "cookies", "salad", "mediterranean", "quick"]


def _bootstrap_guest_account() -> None:
    db = SessionLocal()
    try:
        guest = _get_or_create_guest(db)
        cookbook = _get_or_create_cookbook(db, guest.id)
        tag_objs = _get_or_create_tags(db, guest.id)
        _seed_recipes(db, guest.id, cookbook.id, tag_objs)
        db.commit()
    finally:
        db.close()


def _get_or_create_guest(db):
    guest_email = settings.DEFAULT_GUEST_EMAIL.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == guest_email).first()
    if existing:
        return existing
    guest = User(
        email=guest_email,
        hashed_password=hash_password(settings.DEFAULT_GUEST_PASSWORD),
        display_name=settings.DEFAULT_GUEST_DISPLAY_NAME,
        role=Role.user,
        is_active=1,
        is_approved=1,
        must_change_password=0,
        is_readonly=1,
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


def _get_or_create_cookbook(db, guest_id):
    cookbook = db.query(Cookbook).filter(
        Cookbook.owner_id == guest_id, Cookbook.name == "Sample Recipes"
    ).first()
    if cookbook:
        return cookbook
    cookbook = Cookbook(
        name="Sample Recipes",
        description="Starter recipes for the guest account",
        store=Store.local,
        owner_id=guest_id,
    )
    db.add(cookbook)
    db.commit()
    db.refresh(cookbook)
    return cookbook


def _get_or_create_tags(db, guest_id):
    tag_objs = {}
    for tag_name in SEED_TAGS:
        tag = db.query(Tag).filter(Tag.owner_id == guest_id, Tag.name == tag_name).first()
        if not tag:
            tag = Tag(owner_id=guest_id, name=tag_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        tag_objs[tag_name] = tag
    return tag_objs


def _get_or_create_recipe(db, seed, guest_id, cookbook_id):
    recipe = db.query(Recipe).filter(
        Recipe.owner_id == guest_id, Recipe.title == seed["title"]
    ).first()
    if recipe:
        return recipe
    recipe = Recipe(
        title=seed["title"],
        description=seed["description"],
        ingredients=seed["ingredients"],
        instructions=seed["instructions"],
        store=Store.local,
        owner_id=guest_id,
        cookbook_id=cookbook_id,
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
    return recipe


def _get_or_create_recipe_tag(db, recipe_id, tag_id):
    existing = db.query(RecipeTag).filter(
        RecipeTag.recipe_id == recipe_id, RecipeTag.tag_id == tag_id
    ).first()
    if not existing:
        db.add(RecipeTag(recipe_id=recipe_id, tag_id=tag_id))


def _get_or_create_grocery_list(db, recipe_id, guest_id, title):
    grocery_list = db.query(GroceryList).filter(
        GroceryList.owner_id == guest_id, GroceryList.name == title
    ).first()
    if grocery_list:
        return grocery_list
    grocery_list = GroceryList(name=title, owner_id=guest_id)
    db.add(grocery_list)
    db.commit()
    db.refresh(grocery_list)
    return grocery_list


def _seed_recipes(db, guest_id, cookbook_id, tag_objs):
    for seed in SEED_RECIPES:
        recipe = _get_or_create_recipe(db, seed, guest_id, cookbook_id)
        _tag_recipe(db, recipe.id, seed, tag_objs)
        grocery_list = _get_or_create_grocery_list(
            db, recipe.id, guest_id, f"{seed['title']} Ingredients")
        _add_grocery_items(db, recipe, grocery_list, guest_id)
        _add_note(db, recipe.id, seed["instructions"], guest_id)


def _tag_recipe(db, recipe_id, seed, tag_objs):
    for tag_name in SEED_TAGS:
        if tag_name in seed["title"].lower() or tag_name in (seed.get("category", "") + " " + seed.get("subcategory", "")).lower():
            _get_or_create_recipe_tag(db, recipe_id, tag_objs[tag_name].id)


def _add_grocery_items(db, recipe, grocery_list, guest_id):
    for line in recipe.ingredients.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0].isdigit() or stripped[0] in ('½', '¼', '¾'):
            name_part = stripped
            for prefix in ('1 ', '2 ', '3 ', '4 ', '½ ', '¼ ', '¾ ', '1/2 ', '1/4 '):
                if stripped.startswith(prefix):
                    name_part = stripped[len(prefix):]
                    break
            existing = db.query(GroceryItem).filter(
                GroceryItem.list_id == grocery_list.id,
                GroceryItem.recipe_id == recipe.id,
                GroceryItem.name == name_part,
            ).first()
            if not existing:
                db.add(GroceryItem(
                    list_id=grocery_list.id,
                    recipe_id=recipe.id,
                    name=name_part,
                    owner_id=guest_id,
                ))


def _add_note(db, recipe_id, instructions, guest_id):
    existing = db.query(Note).filter(
        Note.recipe_id == recipe_id, Note.owner_id == guest_id
    ).first()
    if not existing:
        pro_tip = instructions.splitlines()[0] if instructions else 'Enjoy!'
        db.add(Note(
            recipe_id=recipe_id,
            owner_id=guest_id,
            body=f"Pro tip: {pro_tip}",
        ))
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
async def readonly_guest_middleware(request: Request, call_next):
    """Block write operations for read-only (guest/demo) accounts."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                email = payload.get("sub")
                db = SessionLocal()
                user = db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()
                db.close()
                if user and user.is_readonly:
                    return JSONResponse(status_code=403, content={"detail": "Guest account is read-only"})
            except Exception:
                pass
    return await call_next(request)


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
