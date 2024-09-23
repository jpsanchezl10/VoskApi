import os
import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI, WebSocket, Request, Form, Response,HTTPException, Header

from dotenv import load_dotenv
from src.vosk_server.vosk_server import VoskStreamingTranscription,VoskBatchTranscription
import io
import wave
from fastapi.responses import JSONResponse


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Create the FastAPI instance with the configuration options
app_config = {
    'docs_url': None,  # Disable docs (Swagger UI)
    'redoc_url': None  # Disable redoc
}
application = FastAPI(
    title="Virtual Scale Vosk",
    version="1.0",
    **app_config
)

# CORS settings
origins = ["*"]  # Allows all origins; specify your frontend's domain for more security
application.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


VOSK_API_KEY = os.getenv("VOSK_API_KEY")

PORT = int(os.environ.get('PORT', 8080))

def authenticate(token: str):
    return token == VOSK_API_KEY


@application.websocket("/v1/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        token = websocket.headers.get("Authorization")
        if not token or not authenticate(token.split()[-1]):
            await websocket.close(code=1008)
            return

        # Get language from query parameters
        language = websocket.query_params.get("language", "en")

        connection = VoskStreamingTranscription(websocket, language)
        await connection.start()

    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {str(e)}")
        await websocket.close()


@application.post("/v1/transcribe")
async def transcribe_full_audio(
    request: Request,
    language: str = None,
    diarize: bool = False,
    authorization: str = Header(None)
):
    # Extract token from Authorization header
    token = authorization.split()[-1] if authorization else None

    if not token or not authenticate(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get language from query parameters, defaulting to 'en'
    language = language or 'en'
    if language not in ['en', 'es']:
        raise HTTPException(status_code=400, detail="Unsupported language")

    try:
        # Read raw binary data from the request body
        contents = await request.body()

        with io.BytesIO(contents) as buf, wave.open(buf, 'rb') as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 16000:
                return JSONResponse(status_code=400, content={"error": "Audio must be 16kHz mono PCM"})
            
            audio_data = wav.readframes(wav.getnframes())

        transcription = VoskBatchTranscription(language, diarize)
        result = transcription.transcribe(audio_data)

        return JSONResponse(content=result)

    except Exception as e:
        logging.error(f"Error in transcribe_full_audio: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=80,workers=1)