
import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://16.171.147.164:8000/f1/process-telemetry/2021/1?frame_skip=1"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket successfully!")
            try:
                msg = await websocket.recv()
                print(f"Received message: {msg}")
            except websockets.exceptions.ConnectionClosedOK:
                print("Connection closed normally.")
            except Exception as e:
                print(f"Error receiving message: {e}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
