Here’s a modified and streamlined version of the README for GitHub, incorporating the new details and simplifying the content for clarity:

---

# Vosk API: Free and Scalable Speech Recognition Alternative to Deepgram

The Vosk API offers a **free** and highly scalable speech-to-text solution, serving as an excellent alternative to Deepgram. This project uses **Vosk API** alongside **Starlette WebSockets**, enabling **real-time transcription** for over 100 concurrent requests (machine-dependent). You can select between **small** and **medium** models to balance **accuracy** and **performance** based on your needs.

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
   git clone <your-repo-url>
   cd <your-repo-name>
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
        uri="wss://vosk.virtualscale.xyz/v1/stream?language=en&model=medium",
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
    uri=f"wss://vosk.virtualscale.xyz/v1/stream?language=en&model=small",
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
