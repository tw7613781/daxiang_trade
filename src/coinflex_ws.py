import websockets
import asyncio
import hmac
import base64
import hashlib
import json
import os
from dotenv import load_dotenv
from utils import current_milli_ts

load_dotenv()

api_key = os.getenv('APIKEY')
api_secret = os.getenv('APISECRET')

websocket_endpoint = 'wss://v2api.coinflex.com/v2/websocket'

def authMsg():
  ts = current_milli_ts()
  sig_payload = (ts + 'GET/auth/self/verify').encode('utf-8')
  signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), sig_payload, hashlib.sha256).digest()).decode('utf-8')
  return {
    'op': 'login',
    'tag': 1,
    'data': {
      'apiKey': api_key,
      'timestamp': ts,
      'signature': signature
      }
  }

async def process():
  async with websockets.connect(websocket_endpoint) as ws:
    await ws.send(json.dumps(authMsg()))
    while ws.open:
      resp = await ws.recv()
      print(resp)

if __name__ == '__main__':
  asyncio.get_event_loop().run_until_complete(process())