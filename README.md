# Vosk API: Free and Scalable Speech Recognition Alternative to Deepgram

The Vosk API offers a **free** and highly scalable speech-to-text solution, serving as an excellent alternative to Deepgram. This project uses **Vosk Toolkit** alongside **Starlette WebSockets**, enabling **real-time transcription** for over 100 concurrent requests (machine-dependent). You can select between **small** and **medium** models to balance **accuracy** and **performance** based on your needs.

## Features

- **Free and Open-Source**: No subscription required.
- **Real-Time Transcription**: Supports live audio streams via WebSocket.
- **Concurrent Requests**: Handles 100+ requests on suitable hardware.
- **Flexible Models**: Choose between small (faster) or medium (more accurate) models.
- **Multilingual Support**: Works with various languages.
- **Offline Capability**: Internet-free operation with pre-downloaded models.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/jpsanchezl10/VoskApi.git
   cd VoskApi
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download and configure the Vosk models as required.

## Quick Start

1. **Run the WebSocket server**:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Connect to the WebSocket** at `wss://<your-server>/v1/stream`. 

   Use query parameters like:
   - `language` (e.g., `en` for English)
   - `model` (`small` or `medium` for performance vs. accuracy).

3. **Send Audio** in real-time and receive transcriptions.

### Example: Using the VoskBridge Class

The `VoskBridge` class simplifies interacting with the WebSocket. Here’s an example of how to use it:

```python
import asyncio
from vosk_bridge import VoskBridge

async def on_message(message):
    print("Transcription:", message)

async def main():
    bridge = VoskBridge(
        uri="ws://localhost/v1/stream?language=en&model=medium",
        extra_headers={'Authorization': f'Token YOUR_API_KEY'},
        on_message=on_message
    )
    await bridge.start()

    # Simulate sending audio chunks
    with open("sample.raw", "rb") as f:
        while chunk := f.read(4000):  # Adjust chunk size as needed
            bridge.add_request(chunk)

    await bridge.close()

asyncio.run(main())
```

### Key Functions in `VoskBridge`

- **`connect()`**: Establish a WebSocket connection to the server.
- **`add_request(buffer)`**: Add audio chunks to the queue for transcription.
- **`close()`**: Gracefully close the WebSocket connection.
- **`on_message`**: Callback for processing transcription results.

### Real-World Integration

In your app, create a `VoskBridge` instance and start it as an asynchronous task:

```python
bridge = VoskBridge(
    uri=f"ws://localhost/v1/stream?language=en&model=small",
    extra_headers={'Authorization': f'Token {VOSK_API_KEY}'},
    on_message=on_message
)
asyncio.create_task(bridge.start())
```

Send audio chunks with:

```python
bridge.add_request(audio_chunk.raw_data)
```

Close the connection when done:

```python
await bridge.close()
```


### `VoskBridge` Class Example
```python
import asyncio
import websockets
import logging

class VoskBridge:
    def __init__(self, uri, extra_headers, on_message):
        self.uri = uri
        self.extra_headers = extra_headers
        self._on_message = on_message
        self.websocket = None
        self._queue = asyncio.Queue()
        self._ended = False

    async def connect(self):
        logging.info("Connecting to Vosk WebSocket")
        self.websocket = await websockets.connect(self.uri, extra_headers=self.extra_headers)
        logging.info("Connected to Vosk WebSocket")

    async def start(self):
        await self.connect()
        logging.info("Starting Vosk bridge")
        send_task = asyncio.create_task(self.send_audio_stream())
        receive_task = asyncio.create_task(self.receive_message_stream())
        await asyncio.gather(send_task, receive_task)

    async def send_audio_stream(self):
        logging.info("Starting audio stream sending")
        try:
            while not self._ended:
                chunk = await self._queue.get()
                if chunk is None:
                    break
                await self.websocket.send(chunk)
                self._queue.task_done()
        except Exception as e:
            logging.error(f"Error in send_audio_stream: {e}")
        finally:
            logging.info("Finished sending audio stream")

    async def receive_message_stream(self):
        logging.info("Starting message receiving stream")
        try:
            while not self._ended:
                message = await self.websocket.recv()
                await self._on_message(message)
        except websockets.exceptions.ConnectionClosed:
            logging.info("WebSocket connection closed")
        except Exception as e:
            logging.error(f"Error in receive_message_stream: {e}")
        finally:
            logging.info("Finished receiving message stream")

    def add_request(self, buffer):
        self._queue.put_nowait(buffer)

    async def close(self):
        self._ended = True
        await self._queue.put(None)  # Signal to end the send_audio_stream
        if self.websocket:
            await self.websocket.close()
        logging.info("Vosk bridge closed")

    async def run(self):
        await self.start()
```
**Default API KEY*
```sk-lkjfdhfihjsdhfnnser93hklfdlsknfjsdlfakfjuiafyu23080ahkjndfnbsckerpeproyita9837```
