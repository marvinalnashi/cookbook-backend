from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "cookbook.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            occasion TEXT,
            ingredients TEXT,
            steps TEXT
        )
    ''')

    conn.commit()
    conn.close()


init_db()


class Recipe(BaseModel):
    name: str
    description: str
    occasion: str
    ingredients: list[str]
    steps: list[str]


@app.get("/")
async def root():
    return {"message": "Welcome to Little Chef's Cookbook!"}


@app.get("/ping")
async def pong():
    return {"message": "pong"}


@app.post("/recipes/")
async def add_recipe(recipe: Recipe):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO recipes (name, description, occasion, ingredients, steps)
        VALUES (?, ?, ?, ?, ?)
    ''', (recipe.name, recipe.description, recipe.occasion, ",".join(recipe.ingredients), "\n".join(recipe.steps)))

    conn.commit()
    conn.close()

    return {"message": "Recipe added successfully"}


@app.get("/recipes/")
async def get_recipes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes")

    recipes = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0], "name": r[1], "description": r[2], "occasion": r[3],
            "ingredients": r[4].split(","), "steps": r[5].split("\n")
        } for r in recipes
    ]


@app.get("/recipes/filter/")
async def filter_recipes(occasion: str = None, include: str = "", exclude: str = ""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = "SELECT * FROM recipes WHERE 1=1"
    params = []

    if occasion:
        query += " AND occasion = ?"
        params.append(occasion)

    recipes = cursor.execute(query, params).fetchall()
    conn.close()

    filtered_recipes = []
    for r in recipes:
        ingredients = r[4].split(",")
        if any(i in ingredients for i in exclude.split(",")):
            continue
        if include and not any(i in ingredients for i in include.split(",")):
            continue

        filtered_recipes.append({
            "id": r[0], "name": r[1], "description": r[2], "occasion": r[3],
            "ingredients": ingredients, "steps": r[5].split("\n")
        })

    return filtered_recipes
