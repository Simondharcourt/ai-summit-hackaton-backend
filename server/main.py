from fastapi import FastAPI, WebSocket

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
        websocket.send_json({
            "type": "token",
            "content": message
        })

    async def update_bilan(bilan):
        websocket.send_json(bilan)

    demandeur.mainloop(
        wait_message,
        send_message,
        update_bilan
    )
