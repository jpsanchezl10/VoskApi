import asyncio
import websockets
import json
import vosk
import os
from collections import defaultdict

# Load models
VOSK_MODEL_PATH_EN = './vosk-model-small-en-us-0.15'
VOSK_MODEL_PATH_ES = './vosk-model-small-es-0.42'

model_en = vosk.Model(VOSK_MODEL_PATH_EN)
model_es = vosk.Model(VOSK_MODEL_PATH_ES)

models = {
    'en': model_en,
    'es': model_es
}

API_KEY = "your_api_key_here"

async def recognize_audio(websocket, path):
    try:
        # Extract language from path
        language = path.split('=')[-1]
        if language not in models:
            await websocket.send(json.dumps({"error": "Unsupported language"}))
            return

        rec = vosk.KaldiRecognizer(models[language], 16000)
        
        async for message in websocket:
            audio_data = message
            if rec.AcceptWaveform(audio_data):
                result = json.loads(rec.Result())
                response = {
                    "duration": result.get("duration", 0.0),
                    "start": result.get("start", 0.0),
                    "is_final": True,
                    "speech_final": True,
                    "channel": {
                        "alternatives": [
                            {
                                "transcript": result["text"]
                            }
                        ]
                    }
                }
            else:
                partial = json.loads(rec.PartialResult())
                response = {
                    "duration": 0.0,
                    "start": 0.0,
                    "is_final": True,
                    "speech_final": False,
                    "channel": {
                        "alternatives": [
                            {
                                "transcript": partial["partial"]
                            }
                        ]
                    }
                }
            
            await websocket.send(json.dumps(response))
    
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")

def authenticate(headers):
    token = headers.get('Authorization')
    if token:
        token = token.split()[-1]  # Extract token from "Token API_KEY"
        return token == API_KEY
    return False

async def server(websocket, path):
    if not authenticate(websocket.request_headers):
        await websocket.close(1008, "Invalid API key")
        return
    
    await recognize_audio(websocket, path)

start_server = websockets.serve(server, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()