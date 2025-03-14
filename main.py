from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

recipes_db = [
    {
        "id": 1,
        "title": "Tomato Soup",
        "description": "A warm and comforting tomato soup.",
        "steps": ["Chop tomatoes", "Boil with spices", "Blend until smooth"],
        "ingredients": ["Tomato", "Salt", "Garlic"],
        "occasion": "Lunch"
    },
    {
        "id": 2,
        "title": "Grilled Cheese Sandwich",
        "description": "A crispy sandwich with melted cheese.",
        "steps": ["Butter bread", "Add cheese", "Grill until golden"],
        "ingredients": ["Cheese", "Bread", "Butter"],
        "occasion": "Breakfast"
    },
    {
        "id": 3,
        "title": "Beef Stew",
        "description": "A hearty and flavorful beef stew.",
        "steps": ["Brown beef", "Add vegetables", "Simmer until tender"],
        "ingredients": ["Beef", "Potato", "Carrot", "Garlic"],
        "occasion": "Dinner"
    },
]


class Recipe(BaseModel):
    title: str
    description: str
    steps: List[str]
    ingredients: List[str]
    occasion: str


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/recipes")
async def get_recipes(
        included_ingredients: Optional[List[str]] = Query(None),
        excluded_ingredients: Optional[List[str]] = Query(None),
):
    filtered_recipes = recipes_db

    if included_ingredients:
        filtered_recipes = [
            recipe for recipe in filtered_recipes
            if any(ingredient in recipe["ingredients"] for ingredient in included_ingredients)
        ]

    if excluded_ingredients:
        filtered_recipes = [
            recipe for recipe in filtered_recipes
            if not any(ingredient in recipe["ingredients"] for ingredient in excluded_ingredients)
        ]

    return filtered_recipes


@app.post("/recipes/add")
async def add_recipe(recipe: Recipe):
    new_id = max(recipe["id"] for recipe in recipes_db) + 1 if recipes_db else 1
    new_recipe = recipe.dict()
    new_recipe["id"] = new_id
    recipes_db.append(new_recipe)
    return {"message": "Recipe added successfully", "recipe": new_recipe}
