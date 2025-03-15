from fastapi import FastAPI, HTTPException
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


def insert_sample_recipes():
    """Insert sample recipes into the database if none exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()[0]

    if count == 0:
        logging.info("Inserting sample recipes...")

        sample_recipes = [
            {
                "title": "Pancakes",
                "description": "Fluffy breakfast pancakes.",
                "occasion": "Breakfast",
                "ingredients": ["Milk", "Butter", "Eggs"],
                "steps": ["Mix ingredients", "Cook on pan", "Serve"]
            },
            {
                "title": "Grilled Steak",
                "description": "Juicy grilled steak with seasoning.",
                "occasion": "Dinner",
                "ingredients": ["Beef", "Salt", "Pepper"],
                "steps": ["Season steak", "Grill for 5 mins per side", "Serve"]
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


class RecipeFilterRequest(BaseModel):
    occasion: str
    include: List[str] = []
    exclude: List[str] = []


@app.post("/recipes/filter")
def filter_recipes(request: RecipeFilterRequest):
    conn = sqlite3.connect("cookbook.db")
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
                SELECT recipe_id FROM recipe_ingredients WHERE ingredient IN ({})
            )
        """.format(",".join(["?"] * len(request.exclude)))
        query += exclude_query
        params.extend(request.exclude)

    cursor.execute(query, params)
    recipes = cursor.fetchall()
    conn.close()

    return [{"id": row[0], "title": row[1], "description": row[2]} for row in recipes]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
