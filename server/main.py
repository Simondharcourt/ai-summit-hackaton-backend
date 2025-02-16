from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv

load_dotenv()

from demandeur.main import Demandeur

app = FastAPI()


@app.get("/")
async def get():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    demandeur = Demandeur()

    async def wait_message():
        raw_message = await websocket.receive_text()
        return raw_message

    async def send_message(message):
        await websocket.send_json({"type": "message", "content": message})

    async def update_bilan(bilan):
        await websocket.send_json({"type": "update", "content": bilan})

    await demandeur.mainloop(wait_message, send_message, update_bilan)
