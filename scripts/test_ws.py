
import asyncio
import websockets
import ssl
import uuid

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTEwMDMiLCJlbWFpbCI6InByb2Zlc3Npb25hbEB0ZXN0LnZkcml2ZS5pbiIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ3b3Jrc3BhY2VfaWQiOiJiNDU4ZTljZC00NTgxLTQ0ZTItYjljZi1jODA4YWZiYWJmNjQiLCJleHAiOjE3Njg1MDU0ODcsImlhdCI6MTc2ODUwNDU4NywidHlwZSI6ImFjY2VzcyJ9.nTtyMOceQpSWxs55EYn44gjpBiszPTCO5WBy9NqjVqo"
gallery_id = str(uuid.uuid4()) # Valid UUID
uri = f"ws://localhost:8004/api/v1/ws/gallery/{gallery_id}?token={token}"

async def test_ws():
    print(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            print("SUCCESS: Connected to WebSocket!")
            response = await websocket.recv()
            print(f"Received: {response}")
            await websocket.close()
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"FAILURE: Status Code {e.status_code}")
    except Exception as e:
        print(f"FAILURE: {e}")

asyncio.run(test_ws())
