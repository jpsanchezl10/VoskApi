import vosk
import json
from fastapi import WebSocket, WebSocketDisconnect
import logging
from vosk import Model, KaldiRecognizer, SpkModel
import numpy as np

# Load models
VOSK_MODEL_PATH_EN = './src/models/small/vosk-model-small-en-us-0.15'
VOSK_MODEL_PATH_ES = './src/models/small/vosk-model-small-es-0.42'

model_en = vosk.Model(VOSK_MODEL_PATH_EN)
model_es = vosk.Model(VOSK_MODEL_PATH_ES)

models = {
    'en': model_en,
    'es': model_es
}

class VoskStreamingTranscription:
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





class VoskBatchTranscription:
    def __init__(self, language: str, diarize: bool = False):
   
        # Initialize the recognizer
        self.rec = vosk.KaldiRecognizer(models[language], 16000)
        self.rec.SetMaxAlternatives(1)

        # Load and set the speaker model if diarization is requested
        if diarize:
            try:
                # Paths to models
                SPK_MODEL_PATH = "./src/models/speaker_identification/vosk-model-spk-0.4"

                #init the model
                self.spk_model = SpkModel(SPK_MODEL_PATH)
                self.rec.SetSpkModel(self.spk_model)
            except Exception as e:
                print(f"Error loading speaker model: {str(e)}")
                raise

        self.diarize = diarize

    def transcribe(self, audio_data: bytes) -> dict:
        if self.rec.AcceptWaveform(audio_data):
            result = json.loads(self.rec.FinalResult())
            alternatives = result.get("alternatives", [])
            transcript = alternatives[0].get("text", "") if alternatives else ""
            confidence = alternatives[0].get("confidence", 0) if alternatives else 0
            
            response = {
                "duration": result.get("duration", 0.0),
                "is_final": True,
                "speech_final": True,
                "channel": {
                    "alternatives": [
                        {"transcript": transcript, "confidence": confidence}
                    ]
                }
            }
            
            if self.diarize and "spk" in result:
                response["speaker"] = {
                    "x_vector": result["spk"],
                    "frames": result.get("spk_frames", 0)
                }
            
            return response
        return {"error": "Failed to transcribe audio"}

    @staticmethod
    def cosine_dist(x, y):
        nx = np.array(x)
        ny = np.array(y)
        return 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)
