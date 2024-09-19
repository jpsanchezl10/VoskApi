import asyncio
import websockets
import pyaudio
import json

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class VoskClient:
    def __init__(self):
        self.uri = "ws://localhost:80/v1/language=en"
        self.extra_headers = {
            'Authorization': 'Token your_api_key_here'
        }
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri, extra_headers=self.extra_headers)

    async def on_message(self, message):
        result = json.loads(message)

        # print(result)
        sentence = result['channel']['alternatives'][0]['transcript']
        
        confidence = result['channel']['alternatives'][0]['confidence']

        if len(sentence) == 0:
            return
            
        if result['is_final']:
            print("Final: ",sentence)
            print(confidence)
        else:
            print(f"Interim: ",sentence)

    async def start(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("* Recording")

        try:
            await self.connect()
            
            while True:
                try:
                    # Read audio data from microphone
                    data = stream.read(CHUNK)
                    # Send audio data to server
                    await self.websocket.send(data)
                    
                    # Receive and process message
                    message = await self.websocket.recv()
                    await self.on_message(message)
                except KeyboardInterrupt:
                    print("\nStopping...")
                    break
        finally:
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            if self.websocket:
                await self.websocket.close()
            print("* Stopped recording")

async def main():
    client = VoskClient()
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())