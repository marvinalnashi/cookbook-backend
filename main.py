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
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM recipes")
    if cursor.fetchone()[0] > 0:
        logging.info("Sample recipes already exist. Skipping insertion.")
        conn.close()
        return

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
    logging.info("Sample recipes inserted successfully.")


@app.get("/ping")
def ping():
    return {"message": "pong"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
