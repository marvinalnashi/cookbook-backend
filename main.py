from fastapi import FastAPI, HTTPException, Query
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
    yield
    logging.info("Shutting down application...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/ping")
def ping():
    return {"message": "pong"}


class Recipe(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    occasion: str
    ingredients: List[str]
    steps: List[str]


@app.get("/recipes/")
def get_recipes(
        occasion: Optional[str] = None,
        included_ingredients: Optional[List[str]] = Query(None),
        excluded_ingredients: Optional[List[str]] = Query(None),
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT recipes.id, recipes.title, recipes.description 
        FROM recipes 
        JOIN recipe_ingredients ON recipes.id = recipe_ingredients.recipe_id
    """
    params = []

    if occasion:
        query += " WHERE recipes.occasion = ?"
        params.append(occasion)

    if included_ingredients:
        if not params:
            query += " WHERE "
        else:
            query += " AND "
        query += " (" + " OR ".join(["recipe_ingredients.ingredient = ?"] * len(included_ingredients)) + ")"
        params.extend(included_ingredients)

    if excluded_ingredients:
        query += " AND NOT EXISTS (SELECT 1 FROM recipe_ingredients ri WHERE ri.recipe_id = recipes.id AND (" + " OR ".join(
            ["ri.ingredient = ?"] * len(excluded_ingredients)) + "))"
        params.extend(excluded_ingredients)

    cursor.execute(query, params)
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


@app.post("/recipes/add")
def add_recipe(recipe: Recipe):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO recipes (title, description, occasion) VALUES (?, ?, ?)",
                   (recipe.title, recipe.description, recipe.occasion))
    recipe_id = cursor.lastrowid

    for ingredient in recipe.ingredients:
        cursor.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient) VALUES (?, ?)", (recipe_id, ingredient))

    for i, step in enumerate(recipe.steps):
        cursor.execute("INSERT INTO recipe_steps (recipe_id, step_number, instruction) VALUES (?, ?, ?)",
                       (recipe_id, i + 1, step))

    conn.commit()
    conn.close()

    return {"message": "Recipe added successfully"}


@app.post("/recipes/filter")
def filter_recipes(occasion: str, include: List[str] = [], exclude: List[str] = []):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT recipes.id, recipes.title, recipes.description 
        FROM recipes 
        JOIN recipe_ingredients ON recipes.id = recipe_ingredients.recipe_id 
        WHERE recipes.occasion = ?
    """
    params = [occasion]

    if include:
        include_query = " AND (" + " OR ".join(["recipe_ingredients.ingredient = ?"] * len(include)) + ")"
        query += include_query
        params.extend(include)

    if exclude:
        exclude_query = " AND NOT EXISTS (SELECT 1 FROM recipe_ingredients WHERE recipe_ingredients.recipe_id = recipes.id AND (" + " OR ".join(
            ["recipe_ingredients.ingredient = ?"] * len(exclude)) + "))"
        query += exclude_query
        params.extend(exclude)

    cursor.execute(query, params)
    recipes = cursor.fetchall()

    conn.close()
    return [{"id": row["id"], "title": row["title"], "description": row["description"]} for row in recipes]


def insert_sample_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM recipes")
    cursor.execute("DELETE FROM recipe_ingredients")
    cursor.execute("DELETE FROM recipe_steps")

    sample_recipes = [
        {
            "title": "Tomato Soup",
            "description": "A warm and comforting tomato soup.",
            "occasion": "Lunch",
            "ingredients": ["Tomato", "Salt", "Garlic"],
            "steps": ["Chop tomatoes", "Boil with spices", "Blend until smooth"]
        },
        {
            "title": "Grilled Cheese Sandwich",
            "description": "A crispy sandwich with melted cheese.",
            "occasion": "Breakfast",
            "ingredients": ["Cheese", "Bread", "Butter"],
            "steps": ["Butter bread", "Add cheese", "Grill until golden"]
        },
        {
            "title": "Beef Stew",
            "description": "A hearty and flavorful beef stew.",
            "occasion": "Dinner",
            "ingredients": ["Beef", "Potato", "Carrot", "Garlic"],
            "steps": ["Brown beef", "Add vegetables", "Simmer until tender"]
        },
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
    conn.close()


insert_sample_recipes()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
