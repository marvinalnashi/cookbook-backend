import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print("Received:", data)
        await websocket.send_text(f"Echo: {data}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)
