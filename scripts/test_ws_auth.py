
import asyncio
import websockets
import ssl
import uuid
import json
import urllib.request
import urllib.error

# 1. Get Fresh Token
login_url = "http://localhost:8006/api/v1/onboarding/auth/login"
credentials = json.dumps({"email": "professional@test.RawDrive.in", "password": "Test@123"}).encode('utf-8')
headers = {'Content-Type': 'application/json'}

print(f"Logging in to {login_url}...")
try:
    req = urllib.request.Request(login_url, data=credentials, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        token = data['access_token']
        print("SUCCESS: Obtained fresh token")
except Exception as e:
    print(f"LOGIN FAILED: {e}")
    exit(1)

# 2. Test WebSocket
gallery_id = str(uuid.uuid4())
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
