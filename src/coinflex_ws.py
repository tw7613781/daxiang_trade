import websockets
import asyncio
import hmac
import base64
import hashlib
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import current_milli_ts, TERM_BLUE, TERM_NFMT

load_dotenv()

api_key = os.getenv('APIKEY')
api_secret = os.getenv('APISECRET')

sell_price = float(os.getenv('SELLPRICE'))
buy_price = float(os.getenv('BUYPRICE'))

websocket_endpoint = 'wss://v2api.coinflex.com/v2/websocket'

def auth_msg():
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

def subscribe_balance_msg():
  return {
    'op': 'subscribe',
    'args': ['balance:all'],
    'tag': 101
  }

def subscribe_orders_msg():
  return {
    'op': 'subscribe', 
    'args': ['order:all'], 
    'tag': 102
  }

def subscribe_ticker_msg(market):
  return {
    'op': 'subscribe', 
    'tag': 1,
    'args': [f'ticker:{market}']
  }

def place_limit_order_msg(market, side, quantity, price):
  return {
    'op': 'placeorder',
    'tag': 123,
    'data': {
      'timestamp': current_milli_ts(),
      'clientOrderId': 1,
      'marketCode': market,
      'side': side,
      'orderType': 'LIMIT',
      'quantity': quantity,
      'price': price
    }
  }

async def process():
  async with websockets.connect(websocket_endpoint) as ws:
    await ws.send(json.dumps(auth_msg()))
    await ws.send(json.dumps(subscribe_orders_msg()))
    await ws.send((json.dumps(subscribe_ticker_msg('FLEX-USD'))))
    # await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'BUY', 1, 4.5)))
    while ws.open:
      resp = await ws.recv()
      msg = json.loads(resp)
      # print(msg)
      if 'event' in msg and msg['event']=='login':
        ts = msg['timestamp']
        print(f'{TERM_BLUE}Login succeed at {datetime.fromtimestamp(int(ts) / 1000)}{TERM_NFMT}')
      if 'table' in msg and msg['table']=='order':
        data = msg['data']
        print(f'{TERM_BLUE}{data}{TERM_NFMT}')
        if 'notice' in data and data['notice'] == 'OrderMatched':
          side = data['side']
          quantity = data['quantity']
          price = data['price']
          if side == 'BUY':
            # 买单成交了,要挂卖单
            await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'SELL', int(quantity * price / sell_price), sell_price)))
          elif side == 'SELL':
            # 卖单成交了,要挂买单
            await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'BUY', int(quantity * price / buy_price), buy_price)))

if __name__ == '__main__':
  asyncio.get_event_loop().run_until_complete(process())