import asyncio
import websockets
import json
import vosk
import os
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

# Load models
VOSK_MODEL_PATH_EN = './vosk-model-small-en-us-0.15'
VOSK_MODEL_PATH_ES = './vosk-model-small-es-0.42'

model_en = vosk.Model(VOSK_MODEL_PATH_EN)
model_es = vosk.Model(VOSK_MODEL_PATH_ES)

models = {
    'en': model_en,
    'es': model_es
}

VOSK_API_KEY = os.getenv("VOSK_API_KEY")

class VoskConnection:
    def __init__(self, websocket, language):
        self.websocket = websocket
        self.rec = vosk.KaldiRecognizer(models[language], 16000)
        self.rec.SetMaxAlternatives(1)

    async def start(self):
        try:
            async for message in self.websocket:
                audio_data = message
                if self.rec.AcceptWaveform(audio_data):
                    result = json.loads(self.rec.Result())


                    alternatives = result.get("alternatives", [])

                    transcript = alternatives[0].get("text", "") if alternatives else ""
                    confidence = alternatives[0].get("confidence", 0) if alternatives else 0

                    if transcript:
                        print(transcript)
                        response = {
                            "duration": result.get("duration", 0.0),
                            "start": result.get("start", 0.0),
                            "is_final": True,
                            "speech_final": True,
                            "channel": {
                                "alternatives": [
                                    {"transcript": transcript, "confidence": confidence}
                                ]
                            }
                        }

                else:
                    partial = json.loads(self.rec.PartialResult())
                    response = {
                        "duration": 0.0,
                        "start": 0.0,
                        "is_final": False,
                        "speech_final": False,
                        "channel": {
                            "alternatives": [
                                {"transcript": partial.get("partial", ""), "confidence": 0}
                            ]
                        }
                    }
                await self.websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")



def authenticate(headers):
    token = headers.get('Authorization')
    if token:
        token = token.split()[-1]  # Extract token from "Token API_KEY"
        return token == VOSK_API_KEY
    return False

async def server(websocket, path):
    if not authenticate(websocket.request_headers):
        await websocket.close(1008, "Invalid API key")
        return
    
    language = path.split('=')[-1]
    if language not in models:
        await websocket.send(json.dumps({"error": "Unsupported language"}))
        return

    connection = VoskConnection(websocket, language)
    await connection.start()


start_server = websockets.serve(server, "localhost", 80)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()