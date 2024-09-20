import vosk
import json
from fastapi import WebSocket, WebSocketDisconnect
import logging

# Load models
VOSK_MODEL_PATH_EN = './src/models/small/vosk-model-small-en-us-0.15'
VOSK_MODEL_PATH_ES = './src/models/small/vosk-model-small-es-0.42'

model_en = vosk.Model(VOSK_MODEL_PATH_EN)
model_es = vosk.Model(VOSK_MODEL_PATH_ES)

models = {
    'en': model_en,
    'es': model_es
}

class VoskConnection:
    def __init__(self, websocket: WebSocket, language: str):
        self.websocket = websocket
        self.rec = vosk.KaldiRecognizer(models[language], 16000)
        self.rec.SetMaxAlternatives(1)

    async def start(self):
        try:
            while True:
                audio_data = await self.websocket.receive_bytes()
                if self.rec.AcceptWaveform(audio_data):
                    result = json.loads(self.rec.Result())
                    alternatives = result.get("alternatives", [])
                    transcript = alternatives[0].get("text", "") if alternatives else ""
                    confidence = alternatives[0].get("confidence", 0) if alternatives else 0
                    if transcript:
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
                await self.websocket.send_json(response)
        except WebSocketDisconnect:
            logging.error("WebSocket connection closed",exc_info=True)
        except Exception as e:
            logging.error(f"Error in VoskConnection: {str(e)}",exc_info=True)