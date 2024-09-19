import asyncio
import websockets
import pyaudio
import json

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

async def send_audio_to_vosk():

    uri = "ws://localhost:80/v1/language=en"
    extra_headers = {
        'Authorization': 'Token your_api_key_here'
    }
    
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* Recording")

    try:
        async with websockets.connect(uri, extra_headers=extra_headers) as websocket:
            while True:
                try:
                    # Read audio data from microphone
                    data = stream.read(CHUNK)
                    
                    # Send audio data to server
                    await websocket.send(data)
                    
                    # Receive and print results
                    response = await websocket.recv()
                    result = json.loads(response)
                    
                    if result['channel']['alternatives'][0]['transcript']:
                        if result['is_final']:
                            print(f"Final: {result['channel']['alternatives'][0]['transcript']}")
                        else:
                            print(f"Interim: {result['channel']['alternatives'][0]['transcript']}")
                    
                except KeyboardInterrupt:
                    print("\nStopping...")
                    break

    finally:
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("* Stopped recording")

asyncio.get_event_loop().run_until_complete(send_audio_to_vosk())