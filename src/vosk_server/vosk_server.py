import json
from fastapi import WebSocket, WebSocketDisconnect
import logging
from vosk import Model, KaldiRecognizer, SpkModel
import numpy as np
import logging
import time

# EN models
VOSK_MODEL_EN_SMALL = Model('./src/models/small/vosk-model-small-en-us-0.15')
VOSK_MODEL_EN_MED = Model('./src/models/med/vosk-model-en-us-daanzu-20200905')

#ES Models
VOSK_MODEL_ES_SMALL = Model( './src/models/small/vosk-model-small-es-0.42')


en_models = {
    'small': VOSK_MODEL_EN_SMALL,
    'medium': VOSK_MODEL_EN_MED
}

es_models = {
    'small':VOSK_MODEL_ES_SMALL,
    'medium': VOSK_MODEL_ES_SMALL 
}

models = {
    'en': en_models,
    'es': es_models
}

def get_model(language, size):
    lang_models = models.get(language)
    
    if lang_models:
        # Try to get the specific size model, return None if not found
        return lang_models.get(size, None)
    return None

class VoskStreamingTranscription:
    def __init__(self, websocket: WebSocket, language: str,size:str = "small"):
        self.websocket = websocket


        model = get_model(language=language,size=size)

        if model:
            self.rec = KaldiRecognizer(model, 16000)
        else:
            self.rec = KaldiRecognizer(Model(VOSK_MODEL_PATH_EN_SMALL),16000)
  
    
        self.rec.SetMaxAlternatives(1)
        self.start_time = None

    async def start(self):
        try:
            while True:
                audio_data = await self.websocket.receive_bytes()
                self.start_time = time.time()
                
                if self.rec.AcceptWaveform(audio_data):
                    result = json.loads(self.rec.Result())
                    alternatives = result.get("alternatives", [])
                    transcript = alternatives[0].get("text", "") if alternatives else ""
                    confidence = alternatives[0].get("confidence", 0) if alternatives else 0
                    if transcript:
                        elapsed_time = time.time() - self.start_time
                        response = {
                            "duration": elapsed_time,
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
                    elapsed_time = time.time() - self.start_time
                    response = {
                        "duration": elapsed_time,
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
    def __init__(self, language: str, diarize: bool = False,size: str = "small"):
        # Initialize the recognizer

        model = get_model(language=language,size=size)

        if model:
            self.rec = KaldiRecognizer(model, 16000)
        else:
            self.rec = KaldiRecognizer(Model(VOSK_MODEL_PATH_EN_SMALL),16000)
            
        self.rec.SetMaxAlternatives(1)
        # Load and set the speaker model if diarization is requested
        if diarize:
            try:
                # Paths to models
                SPK_MODEL_PATH = "./src/models/speaker_identification/vosk-model-spk-0.4"
                # init the model
                self.spk_model = SpkModel(SPK_MODEL_PATH)
                self.rec.SetSpkModel(self.spk_model)
            except Exception as e:
                print(f"Error loading speaker model: {str(e)}")
                raise
        self.diarize = diarize

    def transcribe(self, audio_data: bytes) -> dict:
        start_time = time.time()
        if self.rec.AcceptWaveform(audio_data):
            result = json.loads(self.rec.FinalResult())
            alternatives = result.get("alternatives", [])
            transcript = alternatives[0].get("text", "") if alternatives else ""
            confidence = alternatives[0].get("confidence", 0) if alternatives else 0
            elapsed_time = time.time() - start_time
            response = {
                "duration": elapsed_time,
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