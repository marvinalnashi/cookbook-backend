from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import logging
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import paho.mqtt.client as mqtt
import json
import ssl
import certifi
import os

logging.basicConfig(level=logging.INFO)
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application...")
    setup_database()
    insert_sample_recipes()
    yield
    logging.info("Shutting down application...")


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def on_connect(client, userdata, flags, rc):
    print("Connected to HiveMQ with result code", rc)
    for topic in ["nav/up", "nav/down", "nav/left", "nav/right", "nav/select"]:
        client.subscribe(topic)


def on_message(client, userdata, msg):
    print(f"MQTT: {msg.topic} = {msg.payload}")
    payload = msg.payload.decode()
    asyncio.run(broadcast_ws({"topic": msg.topic, "value": payload}))


mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(
    os.getenv("MQTT_USERNAME", "littlechef"),
    os.getenv("MQTT_PASSWORD", "Cookbook123")
)

mqtt_client.tls_set(
    ca_certs=certifi.where(),
    certfile=None,
    keyfile=None,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("ef137b86ea2944f19a8b1bb71757d7bb.s1.eu.hivemq.cloud", 8883)

mqtt_client.loop_start()


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
            occasion TEXT,
            duration INTEGER
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
                "duration": 5,
                "ingredients": ["Milk", "Butter", "Eggs", "Flour", "Sugar"],
                "steps": ["Mix ingredients", "Cook on pan", "Serve with syrup"]
            },
            {
                "title": "Omelette",
                "description": "Classic omelette with cheese and vegetables.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Eggs", "Cheese", "Tomato", "Butter"],
                "steps": ["Beat eggs", "Cook in butter", "Add cheese and tomato", "Serve"]
            },
            {
                "title": "French Toast",
                "description": "Sweet and crispy French toast.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Bread", "Eggs", "Milk", "Cinnamon"],
                "steps": ["Mix eggs and milk", "Dip bread", "Fry", "Serve with syrup"]
            },
            {
                "title": "Smoothie Bowl",
                "description": "Healthy fruit smoothie bowl.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Banana", "Milk", "Spinach", "Yoghurt"],
                "steps": ["Blend ingredients", "Pour into bowl", "Top with granola"]
            },
            {
                "title": "Avocado Toast",
                "description": "Toasted bread with mashed avocado and tomato.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Bread", "Avocado", "Tomato", "Salt"],
                "steps": ["Toast bread", "Mash avocado", "Add tomato slices", "Serve"]
            },
            {
                "title": "Muffins",
                "description": "Soft and delicious breakfast muffins.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Flour", "Eggs", "Milk", "Sugar", "Butter"],
                "steps": ["Mix ingredients", "Bake at 180°C for 20 mins", "Serve"]
            },
            {
                "title": "Scrambled Eggs",
                "description": "Soft scrambled eggs with butter.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Eggs", "Butter", "Salt", "Pepper"],
                "steps": ["Beat eggs", "Cook in butter", "Season and serve"]
            },
            {
                "title": "Banana Pancakes",
                "description": "Healthy banana-based pancakes.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Banana", "Eggs", "Oats", "Milk"],
                "steps": ["Blend ingredients", "Cook in pan", "Serve"]
            },
            {
                "title": "Egg Benedict",
                "description": "Poached eggs on toasted bread with hollandaise sauce.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Eggs", "Butter", "Bread", "Lemon"],
                "steps": ["Poach eggs", "Toast bread", "Make hollandaise sauce", "Assemble and serve"]
            },
            {
                "title": "Berry Parfait",
                "description": "Layered yoghurt, berries, and granola.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Yoghurt", "Blueberries", "Strawberries", "Granola"],
                "steps": ["Layer ingredients", "Refrigerate for 10 mins", "Serve"]
            },
            {
                "title": "Cinnamon Rolls",
                "description": "Soft rolls with cinnamon sugar filling.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Flour", "Sugar", "Milk", "Cinnamon", "Butter"],
                "steps": ["Make dough", "Add cinnamon filling", "Bake", "Drizzle with icing"]
            },
            {
                "title": "Vegetable Omelette",
                "description": "Egg omelette with fresh vegetables.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Eggs", "Tomato", "Spinach", "Cheese"],
                "steps": ["Beat eggs", "Cook in pan", "Add vegetables", "Fold and serve"]
            },
            {
                "title": "Peanut Butter Toast",
                "description": "Crunchy toast with peanut butter and honey.",
                "occasion": "Breakfast",
                "duration": 5,
                "ingredients": ["Bread", "Peanut Butter", "Honey", "Banana"],
                "steps": ["Toast bread", "Spread peanut butter", "Add banana slices and honey", "Serve"]
            },
            # Lunch Recipes
            {
                "title": "Caesar Salad",
                "description": "Fresh salad with chicken and dressing.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Lettuce", "Chicken", "Cheese", "Croutons"],
                "steps": ["Chop ingredients", "Mix with dressing", "Serve"]
            },
            {
                "title": "Tomato Soup",
                "description": "Creamy homemade tomato soup.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Tomato", "Onion", "Garlic", "Milk"],
                "steps": ["Sauté onion and garlic", "Add tomatoes", "Blend and serve"]
            },
            {
                "title": "Grilled Cheese Sandwich",
                "description": "Crispy sandwich with melted cheese.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Bread", "Cheese", "Butter"],
                "steps": ["Butter bread", "Add cheese", "Grill until golden"]
            },
            {
                "title": "Vegetable Stir-Fry",
                "description": "Stir-fried vegetables with soy sauce.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Carrot", "Tomato", "Broccoli", "Garlic"],
                "steps": ["Chop vegetables", "Stir-fry in pan", "Add soy sauce and serve"]
            },
            {
                "title": "Chicken Wrap",
                "description": "Grilled chicken with vegetables in a wrap.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Chicken", "Lettuce", "Tomato", "Tortilla"],
                "steps": ["Grill chicken", "Wrap with vegetables", "Serve"]
            },
            {
                "title": "Cucumber Sandwich",
                "description": "Light and fresh sandwich with cucumber.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Bread", "Cucumber", "Butter", "Salt"],
                "steps": ["Spread butter on bread", "Add cucumber slices", "Serve"]
            },
            {
                "title": "Club Sandwich",
                "description": "Triple-layered sandwich with chicken and vegetables.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Bread", "Chicken", "Lettuce", "Tomato", "Cheese"],
                "steps": ["Toast bread", "Layer ingredients", "Cut into triangles", "Serve"]
            },
            {
                "title": "Pumpkin Soup",
                "description": "Creamy pumpkin soup with spices.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Pumpkin", "Onion", "Milk", "Salt", "Pepper"],
                "steps": ["Cook pumpkin and onion", "Blend with milk", "Season and serve"]
            },
            {
                "title": "Caprese Salad",
                "description": "Fresh mozzarella, tomato, and basil salad.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Tomato", "Mozzarella", "Basil", "Olive Oil"],
                "steps": ["Slice ingredients", "Arrange on plate", "Drizzle with olive oil", "Serve"]
            },
            {
                "title": "Grilled Chicken Salad",
                "description": "Healthy salad with grilled chicken.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Chicken", "Lettuce", "Cucumber", "Carrot"],
                "steps": ["Grill chicken", "Chop vegetables", "Mix with dressing", "Serve"]
            },
            {
                "title": "Veggie Wrap",
                "description": "A tortilla wrap filled with fresh vegetables.",
                "occasion": "Lunch",
                "duration": 5,
                "ingredients": ["Tortilla", "Tomato", "Cucumber", "Carrot", "Cheese"],
                "steps": ["Chop vegetables", "Wrap ingredients in tortilla", "Serve"]
            },
            # Dinner Recipes
            {
                "title": "Grilled Steak",
                "description": "Juicy grilled steak with seasoning.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Beef", "Salt", "Pepper"],
                "steps": ["Season steak", "Grill for 5 mins per side", "Serve"]
            },
            {
                "title": "Spaghetti Bolognese",
                "description": "Classic pasta with meat sauce.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Spaghetti", "Tomato", "Ground Beef", "Onion"],
                "steps": ["Cook pasta", "Prepare sauce", "Serve"]
            },
            {
                "title": "Mutton Curry",
                "description": "Spiced mutton curry with rice.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Mutton", "Tomato", "Garlic", "Onion"],
                "steps": ["Cook mutton", "Prepare sauce", "Serve with rice"]
            },
            {
                "title": "Pork Chops",
                "description": "Juicy grilled pork chops.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Pork", "Salt", "Garlic"],
                "steps": ["Season pork", "Grill until cooked", "Serve"]
            },
            {
                "title": "Chicken Alfredo",
                "description": "Creamy chicken pasta.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Chicken", "Milk", "Pasta", "Cheese"],
                "steps": ["Cook pasta", "Prepare sauce", "Mix and serve"]
            },
            {
                "title": "Vegetable Stew",
                "description": "Healthy vegetable stew.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Carrot", "Tomato", "Potato", "Onion"],
                "steps": ["Chop vegetables", "Cook until tender", "Serve"]
            },
            {
                "title": "BBQ Ribs",
                "description": "Slow-cooked BBQ ribs with sauce.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Pork", "BBQ Sauce", "Salt", "Garlic"],
                "steps": ["Marinate ribs", "Slow cook for 2 hours", "Brush with BBQ sauce", "Serve"]
            },
            {
                "title": "Beef Stir-Fry",
                "description": "Quick stir-fried beef with vegetables.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Beef", "Broccoli", "Carrot", "Soy Sauce"],
                "steps": ["Slice beef", "Stir-fry with vegetables", "Add soy sauce", "Serve"]
            },
            {
                "title": "Chicken Curry",
                "description": "Spicy chicken curry with rice.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Chicken", "Tomato", "Onion", "Garlic", "Milk"],
                "steps": ["Sauté onions", "Add chicken and spices", "Simmer with tomato and milk", "Serve with rice"]
            },
            {
                "title": "Stuffed Bell Peppers",
                "description": "Bell peppers stuffed with meat and rice.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Bell Peppers", "Ground Beef", "Rice", "Tomato"],
                "steps": ["Hollow peppers", "Stuff with mixture", "Bake and serve"]
            },
            {
                "title": "Lasagna",
                "description": "Layered pasta with beef and cheese.",
                "occasion": "Dinner",
                "duration": 5,
                "ingredients": ["Lasagna Noodles", "Beef", "Tomato Sauce", "Cheese"],
                "steps": ["Prepare sauce", "Layer with pasta and cheese", "Bake", "Serve"]
            },
            # Dessert Recipes
            {
                "title": "Chocolate Cake",
                "description": "Rich chocolate cake with frosting.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Flour", "Sugar", "Milk", "Cocoa Powder"],
                "steps": ["Mix ingredients", "Bake at 180°C for 30 mins", "Frost and serve"]
            },
            {
                "title": "Fruit Salad",
                "description": "Mixed fruit salad with yoghurt.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Banana", "Apple", "Yoghurt", "Honey"],
                "steps": ["Chop fruits", "Mix with yoghurt", "Serve"]
            },
            {
                "title": "Ice Cream Sundae",
                "description": "Ice cream with toppings.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Milk", "Sugar", "Chocolate Syrup"],
                "steps": ["Prepare ice cream", "Add toppings", "Serve"]
            },
            {
                "title": "Cheesecake",
                "description": "Rich and creamy baked cheesecake.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Cream Cheese", "Sugar", "Eggs", "Butter"],
                "steps": ["Mix ingredients", "Bake at 180°C for 45 mins", "Cool and serve"]
            },
            {
                "title": "Strawberry Shortcake",
                "description": "Light cake with strawberries and cream.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Flour", "Sugar", "Strawberries", "Milk"],
                "steps": ["Bake cake", "Slice strawberries", "Layer with cream", "Serve"]
            },
            {
                "title": "Chocolate Chip Cookies",
                "description": "Classic cookies with chocolate chips.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Flour", "Butter", "Sugar", "Chocolate Chips"],
                "steps": ["Mix dough", "Shape cookies", "Bake for 12 mins", "Serve"]
            },
            {
                "title": "Apple Pie",
                "description": "Traditional apple pie with cinnamon.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Apples", "Flour", "Sugar", "Cinnamon", "Butter"],
                "steps": ["Prepare filling", "Roll crust", "Bake for 45 mins", "Serve"]
            },
            {
                "title": "Lemon Tart",
                "description": "Tangy lemon tart with buttery crust.",
                "occasion": "Dessert",
                "duration": 5,
                "ingredients": ["Lemon", "Sugar", "Butter", "Flour"],
                "steps": ["Prepare crust", "Make lemon filling", "Bake and serve"]
            }
        ]

        for recipe in sample_recipes:
            cursor.execute("INSERT INTO recipes (title, description, occasion, duration) VALUES (?, ?, ?, ?)",
                           (recipe["title"], recipe["description"], recipe["occasion"], recipe["duration"]))
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


led_state = {
    "color": "000000",
    "power": "off"
}


class LEDRequest(BaseModel):
    color: str
    power: str


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/")
async def root():
    return {"message": "pong"}


active_connections: List[WebSocket] = []


async def broadcast_led_state():
    """Send LED state update to all connected clients."""
    for connection in active_connections:
        await connection.send_json(led_state)


@app.post("/led/set-color")
async def set_led_color(request: LEDRequest):
    """API endpoint to update LED color and power state."""
    global led_state
    led_state["color"] = request.color
    led_state["power"] = request.power

    await broadcast_led_state()

    return {"message": "LED state updated", "state": led_state}


@app.get("/led/status")
def get_led_status():
    """API endpoint to get the current LED state."""
    return led_state


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            print(f"Received message: {msg}")
            for conn in active_connections:
                if conn != websocket:
                    await conn.send_text(msg)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


async def broadcast_ws(data):
    for ws in websocket_connections:
        try:
            await ws.send_text(json.dumps(data))
        except:
            pass


@app.get("/recipes", include_in_schema=False)
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
            "duration": recipe["duration"],
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
        "duration": recipe["duration"],
        "ingredients": ingredients,
        "steps": steps
    }


class RecipeFilterRequest(BaseModel):
    occasion: str
    include: List[str] = []
    exclude: List[str] = []
    match_all: bool = False


@app.post("/recipes/filter")
def filter_recipes(request: RecipeFilterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM recipes WHERE occasion = ?", (request.occasion,))
    all_recipes = cursor.fetchall()

    filtered_recipes = []
    for recipe in all_recipes:
        cursor.execute("SELECT ingredient FROM recipe_ingredients WHERE recipe_id = ?", (recipe["id"],))
        ingredients = {row["ingredient"] for row in cursor.fetchall()}

        if request.include:
            if request.match_all:
                if not all(inc in ingredients for inc in request.include):
                    continue
            else:
                if not any(inc in ingredients for inc in request.include):
                    continue

        if request.exclude:
            if any(exc in ingredients for exc in request.exclude):
                continue

        filtered_recipes.append({
            "id": recipe["id"],
            "title": recipe["title"],
            "description": recipe["description"],
            "duration": recipe["duration"]
        })

    conn.close()
    return filtered_recipes


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
