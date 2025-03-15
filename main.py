from fastapi import FastAPI, HTTPException
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import logging
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application...")
    setup_database()
    insert_sample_recipes()
    yield
    logging.info("Shutting down application...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cookbook-frontend-seven.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type"],
)


def get_db_connection():
    conn = sqlite3.connect("cookbook.db")
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            occasion TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            step_number INTEGER,
            instruction TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    logging.info("Database setup complete.")


def insert_sample_recipes():
    """Insert sample recipes into the database if none exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()[0]

    if count == 0:
        logging.info("Inserting sample recipes...")

        sample_recipes = [
            # Breakfast Recipes
            {
                "title": "Pancakes",
                "description": "Fluffy breakfast pancakes.",
                "occasion": "Breakfast",
                "ingredients": ["Milk", "Butter", "Eggs", "Flour", "Sugar"],
                "steps": ["Mix ingredients", "Cook on pan", "Serve with syrup"]
            },
            {
                "title": "Omelette",
                "description": "Classic omelette with cheese and vegetables.",
                "occasion": "Breakfast",
                "ingredients": ["Eggs", "Cheese", "Tomato", "Butter"],
                "steps": ["Beat eggs", "Cook in butter", "Add cheese and tomato", "Serve"]
            },
            {
                "title": "French Toast",
                "description": "Sweet and crispy French toast.",
                "occasion": "Breakfast",
                "ingredients": ["Bread", "Eggs", "Milk", "Cinnamon"],
                "steps": ["Mix eggs and milk", "Dip bread", "Fry", "Serve with syrup"]
            },
            {
                "title": "Smoothie Bowl",
                "description": "Healthy fruit smoothie bowl.",
                "occasion": "Breakfast",
                "ingredients": ["Banana", "Milk", "Spinach", "Yoghurt"],
                "steps": ["Blend ingredients", "Pour into bowl", "Top with granola"]
            },
            {
                "title": "Avocado Toast",
                "description": "Toasted bread with mashed avocado and tomato.",
                "occasion": "Breakfast",
                "ingredients": ["Bread", "Avocado", "Tomato", "Salt"],
                "steps": ["Toast bread", "Mash avocado", "Add tomato slices", "Serve"]
            },
            {
                "title": "Muffins",
                "description": "Soft and delicious breakfast muffins.",
                "occasion": "Breakfast",
                "ingredients": ["Flour", "Eggs", "Milk", "Sugar", "Butter"],
                "steps": ["Mix ingredients", "Bake at 180°C for 20 mins", "Serve"]
            },
            {
                "title": "Scrambled Eggs",
                "description": "Soft scrambled eggs with butter.",
                "occasion": "Breakfast",
                "ingredients": ["Eggs", "Butter", "Salt", "Pepper"],
                "steps": ["Beat eggs", "Cook in butter", "Season and serve"]
            },
            {
                "title": "Banana Pancakes",
                "description": "Healthy banana-based pancakes.",
                "occasion": "Breakfast",
                "ingredients": ["Banana", "Eggs", "Oats", "Milk"],
                "steps": ["Blend ingredients", "Cook in pan", "Serve"]
            },
            {
                "title": "Egg Benedict",
                "description": "Poached eggs on toasted bread with hollandaise sauce.",
                "occasion": "Breakfast",
                "ingredients": ["Eggs", "Butter", "Bread", "Lemon"],
                "steps": ["Poach eggs", "Toast bread", "Make hollandaise sauce", "Assemble and serve"]
            },
            {
                "title": "Berry Parfait",
                "description": "Layered yoghurt, berries, and granola.",
                "occasion": "Breakfast",
                "ingredients": ["Yoghurt", "Blueberries", "Strawberries", "Granola"],
                "steps": ["Layer ingredients", "Refrigerate for 10 mins", "Serve"]
            },
            {
                "title": "Cinnamon Rolls",
                "description": "Soft rolls with cinnamon sugar filling.",
                "occasion": "Breakfast",
                "ingredients": ["Flour", "Sugar", "Milk", "Cinnamon", "Butter"],
                "steps": ["Make dough", "Add cinnamon filling", "Bake", "Drizzle with icing"]
            },
            {
                "title": "Vegetable Omelette",
                "description": "Egg omelette with fresh vegetables.",
                "occasion": "Breakfast",
                "ingredients": ["Eggs", "Tomato", "Spinach", "Cheese"],
                "steps": ["Beat eggs", "Cook in pan", "Add vegetables", "Fold and serve"]
            },
            {
                "title": "Peanut Butter Toast",
                "description": "Crunchy toast with peanut butter and honey.",
                "occasion": "Breakfast",
                "ingredients": ["Bread", "Peanut Butter", "Honey", "Banana"],
                "steps": ["Toast bread", "Spread peanut butter", "Add banana slices and honey", "Serve"]
            },
            # Lunch Recipes
            {
                "title": "Caesar Salad",
                "description": "Fresh salad with chicken and dressing.",
                "occasion": "Lunch",
                "ingredients": ["Lettuce", "Chicken", "Cheese", "Croutons"],
                "steps": ["Chop ingredients", "Mix with dressing", "Serve"]
            },
            {
                "title": "Tomato Soup",
                "description": "Creamy homemade tomato soup.",
                "occasion": "Lunch",
                "ingredients": ["Tomato", "Onion", "Garlic", "Milk"],
                "steps": ["Sauté onion and garlic", "Add tomatoes", "Blend and serve"]
            },
            {
                "title": "Grilled Cheese Sandwich",
                "description": "Crispy sandwich with melted cheese.",
                "occasion": "Lunch",
                "ingredients": ["Bread", "Cheese", "Butter"],
                "steps": ["Butter bread", "Add cheese", "Grill until golden"]
            },
            {
                "title": "Vegetable Stir-Fry",
                "description": "Stir-fried vegetables with soy sauce.",
                "occasion": "Lunch",
                "ingredients": ["Carrot", "Tomato", "Broccoli", "Garlic"],
                "steps": ["Chop vegetables", "Stir-fry in pan", "Add soy sauce and serve"]
            },
            {
                "title": "Chicken Wrap",
                "description": "Grilled chicken with vegetables in a wrap.",
                "occasion": "Lunch",
                "ingredients": ["Chicken", "Lettuce", "Tomato", "Tortilla"],
                "steps": ["Grill chicken", "Wrap with vegetables", "Serve"]
            },
            {
                "title": "Cucumber Sandwich",
                "description": "Light and fresh sandwich with cucumber.",
                "occasion": "Lunch",
                "ingredients": ["Bread", "Cucumber", "Butter", "Salt"],
                "steps": ["Spread butter on bread", "Add cucumber slices", "Serve"]
            },
            {
                "title": "Club Sandwich",
                "description": "Triple-layered sandwich with chicken and vegetables.",
                "occasion": "Lunch",
                "ingredients": ["Bread", "Chicken", "Lettuce", "Tomato", "Cheese"],
                "steps": ["Toast bread", "Layer ingredients", "Cut into triangles", "Serve"]
            },
            {
                "title": "Pumpkin Soup",
                "description": "Creamy pumpkin soup with spices.",
                "occasion": "Lunch",
                "ingredients": ["Pumpkin", "Onion", "Milk", "Salt", "Pepper"],
                "steps": ["Cook pumpkin and onion", "Blend with milk", "Season and serve"]
            },
            {
                "title": "Caprese Salad",
                "description": "Fresh mozzarella, tomato, and basil salad.",
                "occasion": "Lunch",
                "ingredients": ["Tomato", "Mozzarella", "Basil", "Olive Oil"],
                "steps": ["Slice ingredients", "Arrange on plate", "Drizzle with olive oil", "Serve"]
            },
            {
                "title": "Grilled Chicken Salad",
                "description": "Healthy salad with grilled chicken.",
                "occasion": "Lunch",
                "ingredients": ["Chicken", "Lettuce", "Cucumber", "Carrot"],
                "steps": ["Grill chicken", "Chop vegetables", "Mix with dressing", "Serve"]
            },
            {
                "title": "Veggie Wrap",
                "description": "A tortilla wrap filled with fresh vegetables.",
                "occasion": "Lunch",
                "ingredients": ["Tortilla", "Tomato", "Cucumber", "Carrot", "Cheese"],
                "steps": ["Chop vegetables", "Wrap ingredients in tortilla", "Serve"]
            },
            # Dinner Recipes
            {
                "title": "Grilled Steak",
                "description": "Juicy grilled steak with seasoning.",
                "occasion": "Dinner",
                "ingredients": ["Beef", "Salt", "Pepper"],
                "steps": ["Season steak", "Grill for 5 mins per side", "Serve"]
            },
            {
                "title": "Spaghetti Bolognese",
                "description": "Classic pasta with meat sauce.",
                "occasion": "Dinner",
                "ingredients": ["Spaghetti", "Tomato", "Ground Beef", "Onion"],
                "steps": ["Cook pasta", "Prepare sauce", "Serve"]
            },
            {
                "title": "Mutton Curry",
                "description": "Spiced mutton curry with rice.",
                "occasion": "Dinner",
                "ingredients": ["Mutton", "Tomato", "Garlic", "Onion"],
                "steps": ["Cook mutton", "Prepare sauce", "Serve with rice"]
            },
            {
                "title": "Pork Chops",
                "description": "Juicy grilled pork chops.",
                "occasion": "Dinner",
                "ingredients": ["Pork", "Salt", "Garlic"],
                "steps": ["Season pork", "Grill until cooked", "Serve"]
            },
            {
                "title": "Chicken Alfredo",
                "description": "Creamy chicken pasta.",
                "occasion": "Dinner",
                "ingredients": ["Chicken", "Milk", "Pasta", "Cheese"],
                "steps": ["Cook pasta", "Prepare sauce", "Mix and serve"]
            },
            {
                "title": "Vegetable Stew",
                "description": "Healthy vegetable stew.",
                "occasion": "Dinner",
                "ingredients": ["Carrot", "Tomato", "Potato", "Onion"],
                "steps": ["Chop vegetables", "Cook until tender", "Serve"]
            },
            {
                "title": "BBQ Ribs",
                "description": "Slow-cooked BBQ ribs with sauce.",
                "occasion": "Dinner",
                "ingredients": ["Pork", "BBQ Sauce", "Salt", "Garlic"],
                "steps": ["Marinate ribs", "Slow cook for 2 hours", "Brush with BBQ sauce", "Serve"]
            },
            {
                "title": "Beef Stir-Fry",
                "description": "Quick stir-fried beef with vegetables.",
                "occasion": "Dinner",
                "ingredients": ["Beef", "Broccoli", "Carrot", "Soy Sauce"],
                "steps": ["Slice beef", "Stir-fry with vegetables", "Add soy sauce", "Serve"]
            },
            {
                "title": "Chicken Curry",
                "description": "Spicy chicken curry with rice.",
                "occasion": "Dinner",
                "ingredients": ["Chicken", "Tomato", "Onion", "Garlic", "Milk"],
                "steps": ["Sauté onions", "Add chicken and spices", "Simmer with tomato and milk", "Serve with rice"]
            },
            {
                "title": "Stuffed Bell Peppers",
                "description": "Bell peppers stuffed with meat and rice.",
                "occasion": "Dinner",
                "ingredients": ["Bell Peppers", "Ground Beef", "Rice", "Tomato"],
                "steps": ["Hollow peppers", "Stuff with mixture", "Bake and serve"]
            },
            {
                "title": "Lasagna",
                "description": "Layered pasta with beef and cheese.",
                "occasion": "Dinner",
                "ingredients": ["Lasagna Noodles", "Beef", "Tomato Sauce", "Cheese"],
                "steps": ["Prepare sauce", "Layer with pasta and cheese", "Bake", "Serve"]
            },
            # Dessert Recipes
            {
                "title": "Chocolate Cake",
                "description": "Rich chocolate cake with frosting.",
                "occasion": "Dessert",
                "ingredients": ["Flour", "Sugar", "Milk", "Cocoa Powder"],
                "steps": ["Mix ingredients", "Bake at 180°C for 30 mins", "Frost and serve"]
            },
            {
                "title": "Fruit Salad",
                "description": "Mixed fruit salad with yoghurt.",
                "occasion": "Dessert",
                "ingredients": ["Banana", "Apple", "Yoghurt", "Honey"],
                "steps": ["Chop fruits", "Mix with yoghurt", "Serve"]
            },
            {
                "title": "Ice Cream Sundae",
                "description": "Ice cream with toppings.",
                "occasion": "Dessert",
                "ingredients": ["Milk", "Sugar", "Chocolate Syrup"],
                "steps": ["Prepare ice cream", "Add toppings", "Serve"]
            },
            {
                "title": "Cheesecake",
                "description": "Rich and creamy baked cheesecake.",
                "occasion": "Dessert",
                "ingredients": ["Cream Cheese", "Sugar", "Eggs", "Butter"],
                "steps": ["Mix ingredients", "Bake at 180°C for 45 mins", "Cool and serve"]
            },
            {
                "title": "Strawberry Shortcake",
                "description": "Light cake with strawberries and cream.",
                "occasion": "Dessert",
                "ingredients": ["Flour", "Sugar", "Strawberries", "Milk"],
                "steps": ["Bake cake", "Slice strawberries", "Layer with cream", "Serve"]
            },
            {
                "title": "Chocolate Chip Cookies",
                "description": "Classic cookies with chocolate chips.",
                "occasion": "Dessert",
                "ingredients": ["Flour", "Butter", "Sugar", "Chocolate Chips"],
                "steps": ["Mix dough", "Shape cookies", "Bake for 12 mins", "Serve"]
            },
            {
                "title": "Apple Pie",
                "description": "Traditional apple pie with cinnamon.",
                "occasion": "Dessert",
                "ingredients": ["Apples", "Flour", "Sugar", "Cinnamon", "Butter"],
                "steps": ["Prepare filling", "Roll crust", "Bake for 45 mins", "Serve"]
            },
            {
                "title": "Lemon Tart",
                "description": "Tangy lemon tart with buttery crust.",
                "occasion": "Dessert",
                "ingredients": ["Lemon", "Sugar", "Butter", "Flour"],
                "steps": ["Prepare crust", "Make lemon filling", "Bake and serve"]
            }
        ]

        for recipe in sample_recipes:
            cursor.execute("INSERT INTO recipes (title, description, occasion) VALUES (?, ?, ?)",
                           (recipe["title"], recipe["description"], recipe["occasion"]))
            recipe_id = cursor.lastrowid

            for ingredient in recipe["ingredients"]:
                cursor.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient) VALUES (?, ?)",
                               (recipe_id, ingredient))

            for i, step in enumerate(recipe["steps"]):
                cursor.execute("INSERT INTO recipe_steps (recipe_id, step_number, instruction) VALUES (?, ?, ?)",
                               (recipe_id, i + 1, step))

        conn.commit()
        logging.info("Sample recipes inserted.")

    conn.close()


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/recipes/")
def get_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()

    response = []
    for recipe in recipes:
        cursor.execute("SELECT ingredient FROM recipe_ingredients WHERE recipe_id=?", (recipe["id"],))
        ingredients = [row["ingredient"] for row in cursor.fetchall()]

        cursor.execute("SELECT instruction FROM recipe_steps WHERE recipe_id=? ORDER BY step_number", (recipe["id"],))
        steps = [row["instruction"] for row in cursor.fetchall()]

        response.append({
            "id": recipe["id"],
            "title": recipe["title"],
            "description": recipe["description"],
            "occasion": recipe["occasion"],
            "ingredients": ingredients,
            "steps": steps
        })

    conn.close()
    return response


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    recipe = cursor.fetchone()

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    cursor.execute("SELECT ingredient FROM recipe_ingredients WHERE recipe_id=?", (recipe["id"],))
    ingredients = [row["ingredient"] for row in cursor.fetchall()]

    cursor.execute("SELECT instruction FROM recipe_steps WHERE recipe_id=? ORDER BY step_number", (recipe["id"],))
    steps = [row["instruction"] for row in cursor.fetchall()]

    conn.close()
    return {
        "id": recipe["id"],
        "title": recipe["title"],
        "description": recipe["description"],
        "occasion": recipe["occasion"],
        "ingredients": ingredients,
        "steps": steps
    }


class RecipeFilterRequest(BaseModel):
    occasion: str
    include: List[str] = []
    exclude: List[str] = []


@app.post("/recipes/filter")
def filter_recipes(request: RecipeFilterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT recipes.id, recipes.title, recipes.description 
        FROM recipes 
        JOIN recipe_ingredients ON recipes.id = recipe_ingredients.recipe_id 
        WHERE recipes.occasion = ?
    """
    params = [request.occasion]

    if request.include:
        include_query = " AND (" + " OR ".join(["recipe_ingredients.ingredient = ?"] * len(request.include)) + ")"
        query += include_query
        params.extend(request.include)

    if request.exclude:
        exclude_query = """
            AND recipes.id NOT IN (
                SELECT recipe_id FROM recipe_ingredients WHERE ingredient IN ({}))
        """.format(",".join(["?"] * len(request.exclude)))
        query += exclude_query
        params.extend(request.exclude)

    cursor.execute(query, params)
    recipes = cursor.fetchall()
    conn.close()

    return [{"id": row[0], "title": row[1], "description": row[2]} for row in recipes]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
