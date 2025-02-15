from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.base import BaseCallbackHandler

from langchain.schema import HumanMessage, AIMessage
from langchain_mistralai import ChatMistralAI

import json

# import os


class WebSocketCallbackHandler(BaseCallbackHandler):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def on_chain_start(self, **kwargs):
        await self.websocket.send_text(json.dumps({"type": "start"}))

    async def on_llm_new_token(self, token: str, **kwargs):
        # Send the new token to the WebSocket client
        await self.websocket.send_text(json.dumps({"type": "token", "content": token}))

    async def on_llm_end(self, response, **kwargs):
        print(response)
        await self.websocket.send_text(json.dumps({"type": "end"}))


app = FastAPI()


@app.get("/")
async def get():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Interactive Mistral Chat</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 600px; margin: auto; }
          #chatbox { white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; height: 300px; overflow-y: auto; }
          input { width: 100%; padding: 10px; }
        </style>
      </head>
      <body>
        <h1>Mistral Chat</h1>
        <div id="chatbox"></div>
        <input id="input" placeholder="Type a message..." autofocus>
        <script>
          const ws = new WebSocket("ws://localhost:8000/ws");
          const chatbox = document.getElementById("chatbox");
          const input = document.getElementById("input");

          ws.onmessage = function(event) {
            const msg = JSON.parse(event)
            if (msg.type === "end") {
              chatbox.innerHTML += "<b>AI:</b> " + msg.content + "<br>";
              chatbox.scrollTop = chatbox.scrollHeight;
            }
          };

          input.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
              const message = input.value;
              chatbox.innerHTML += "<b>You:</b> " + message + "<br>";
              ws.send(message);
              input.value = "";
            }
          });
        </script>
      </body>
    </html>
    """
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Connection openned")

    handler = WebSocketCallbackHandler(websocket)

    callback_manager = CallbackManager([handler])

    print("Linking to AI")
    llm = ChatMistralAI(
        model="mistral-small", streaming=True, callback_manager=callback_manager
    )

    conversation = []

    while True:
        print("Now we talking...")
        user_message = await websocket.receive_text()

        print("User:", user_message)

        conversation.append(HumanMessage(content=user_message))

        response = llm.invoke(conversation)

        print("Ai: ", response.content)
        conversation.append(response)
