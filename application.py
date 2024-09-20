import os
import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI, WebSocket, Request, Form, Response,HTTPException, Header

from dotenv import load_dotenv
from src.vosk_server.vosk_server import VoskConnection

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


@application.websocket("/v1")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        token = websocket.headers.get("Authorization")
        if not token or not authenticate(token.split()[-1]):
            await websocket.close(code=1008)
            return

        # Get language from query parameters
        language = websocket.query_params.get("language", "en")

        connection = VoskConnection(websocket, language)
        await connection.start()

    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {str(e)}")
        await websocket.close()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=80,workers=1)