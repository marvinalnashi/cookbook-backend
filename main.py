import os
import sqlite3
from fastapi import FastAPI, WebSocket
import paho.mqtt.client as mqtt

app = FastAPI()

DB_PATH = "cookbook.db"
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sensors (id INTEGER PRIMARY KEY, name TEXT, value REAL)")
    conn.commit()
else:
    conn = None

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "sensor/data"
client = mqtt.Client()
client.connect(MQTT_BROKER)


@app.get("/")
def root():
    return {"message": "Cookbook Backend Running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if conn:
            cursor.execute("INSERT INTO sensors (name, value) VALUES (?, ?)", ("Sensor", float(data)))
            conn.commit()
        client.publish(MQTT_TOPIC, data)
        await websocket.send_text(f"Received: {data}")
