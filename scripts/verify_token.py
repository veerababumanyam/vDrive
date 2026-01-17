
import jwt
import os

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTEwMDMiLCJlbWFpbCI6InByb2Zlc3Npb25hbEB0ZXN0LnZkcml2ZS5pbiIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ3b3Jrc3BhY2VfaWQiOiJiNDU4ZTljZC00NTgxLTQ0ZTItYjljZi1jODA4YWZiYWJmNjQiLCJleHAiOjE3Njg1MDU0ODcsImlhdCI6MTc2ODUwNDU4NywidHlwZSI6ImFjY2VzcyJ9.nTtyMOceQpSWxs55EYn44gjpBiszPTCO5WBy9NqjVqo"
secret = "40dcb149e40600046f0ff7a67f1c62f1b1111285e917de709bdcc4fcf1c2544d1a7286cfb250312dc3965fdff72a01007482e4cc84fcb22258ed5f5578024ed7"

try:
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    print("SUCCESS: Token verified with .env secret")
    print(decoded)
except Exception as e:
    print(f"FAILURE: {e}")
