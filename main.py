from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://192.168.186.240:3001",
    "https://your-vercel-frontend-url.vercel.app",
    "https://little-chefs-cookbook-production.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    conn = sqlite3.connect("cookbook.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/ping")
def ping():
    return {"message": "pong"}

class Recipe(BaseModel):
    id: Optional[int]
    title: str
    description: str
    occasion: str  # Breakfast, Lunch, Dinner, Dessert
    ingredients: List[str]
    steps: List[str]


@app.on_event("startup")
def startup():
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
        cursor.execute("INSERT INTO recipe_steps (recipe_id, step_number, instruction) VALUES (?, ?, ?)", (recipe_id, i+1, step))

    conn.commit()
    conn.close()

    return {"message": "Recipe added successfully"}


@app.post("/recipes/filter")
def filter_recipes(occasion: str, include: List[str] = [], exclude: List[str] = []):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT DISTINCT recipes.id, recipes.title, recipes.description FROM recipes JOIN recipe_ingredients ON recipes.id = recipe_ingredients.recipe_id WHERE recipes.occasion = ?"
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
