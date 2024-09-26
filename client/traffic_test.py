import asyncio
import wave
import json
from vosk_bridge import VoskBridge, run_bridge
from dotenv import load_dotenv
import os

load_dotenv()

VOSK_API_KEY = os.getenv("VOSK_API_KEY")

# Audio parameters
CHUNK = 1024

class VoskClient:
    def __init__(self, client_id):
        #self.uri = "wss://vosk.virtualscale.xyz/v1/stream?language=en&model=small"
        self.uri = "wss://vosk.virtualscale.xyz/v1/stream?language=en&model=medium"

        self.extra_headers = {
            'Authorization': f'Token {VOSK_API_KEY}'
        }
        self.bridge = None
        self.client_id = client_id

    async def on_message(self, message):
        result = json.loads(message)
        if result is None:
            return
        sentence = result['channel']['alternatives'][0]['transcript']

        if len(sentence) == 0:
            return
        if result['is_final']:
            print(f"Client {self.client_id} Final: {sentence}")

    async def start(self):
        self.bridge = VoskBridge(self.uri, self.extra_headers, self.on_message)
        await run_bridge(self.bridge)

        with wave.open("sample.wav", "rb") as wf:
            print(f"Client {self.client_id}: Started streaming")

            try:
                data = wf.readframes(CHUNK)
                while data:
                    await self.bridge.send_audio(data)
                    await self.bridge.receive_message()
                    data = wf.readframes(CHUNK)
            except Exception as e:
                print(f"Client {self.client_id} Error: {str(e)}")
            finally:
                await self.bridge.close()
                print(f"Client {self.client_id}: Finished streaming")

async def run_client(client_id):
    client = VoskClient(client_id)
    await client.start()

async def main(num_clients):
    tasks = [run_client(i) for i in range(num_clients)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    NUM_CLIENTS = 100  # You can change this to control the number of concurrent clients
    asyncio.run(main(NUM_CLIENTS))