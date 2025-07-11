import asyncio
import pyaudio
import json
from vosk_bridge import VoskBridge, run_bridge
from dotenv import load_dotenv
import os
load_dotenv()


VOSK_API_KEY = os.getenv("VOSK_API_KEY")

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
import base64

class VoskClient:
    def __init__(self):
        self.uri = "ws://localhost/v1/stream?language=en&model=small&authorization=" + base64.b64encode(VOSK_API_KEY.encode()).decode()
        # self.uri = "ws://localhost/v1/stream?language=en&model=small"
        self.bridge = None

    async def on_message(self, message):
        result = json.loads(message)
        if result is None:
            print("result is None")
            return
        sentence = result['channel']['alternatives'][0]['transcript']
        confidence = result['channel']['alternatives'][0]['confidence']
        duration = result['duration']
        if len(sentence) == 0:
            return
        if result['is_final']:
            print("Final: ", sentence)
            print("duration ",duration)
            print(confidence)
        else:
            print(f"Interim: ", sentence)
            ...

    async def start(self):

        self.bridge = VoskBridge(self.uri, self.on_message)
        await run_bridge(self.bridge)

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("* Recording")

        try:
            while True:
                # Read audio data from microphone
                data = stream.read(CHUNK)
                # Send audio data to server
                await self.bridge.send_audio(data)
                # Receive and process message
                await self.bridge.receive_message()
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            await self.bridge.close()
            print("* Stopped recording")

async def main():
    client = VoskClient()
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())