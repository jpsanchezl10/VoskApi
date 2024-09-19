import asyncio
import websockets
import json



class VoskBridge:
    def __init__(self, uri, extra_headers, on_message):
        self.uri = uri
        self.extra_headers = extra_headers
        self.on_message = on_message
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri, extra_headers=self.extra_headers)

    async def send_audio(self, audio_data):
        if self.websocket:
            await self.websocket.send(audio_data)

    async def receive_message(self):
        if self.websocket:
            message = await self.websocket.recv()
            await self.on_message(message)

    async def close(self):
        if self.websocket:
            await self.websocket.close()

async def run_bridge(bridge):
    await bridge.connect()