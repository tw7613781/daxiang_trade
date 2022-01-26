import websockets
import asyncio
import hmac
import base64
import hashlib
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import current_milli_ts, TERM_BLUE, TERM_NFMT, TERM_GREEN, TERM_RED

load_dotenv()

api_key = os.getenv('APIKEY')
api_secret = os.getenv('APISECRET')
user_id = os.getenv('USERID')

sell_price = float(os.getenv('SELLPRICE'))
buy_price = float(os.getenv('BUYPRICE'))
depth_amount = float(os.getenv('DEPTHAMOUNT'))

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

def subscribe_orders_msg(market):
  return {
    'op': 'subscribe', 
    'args': [f'order:{market}'], 
    'tag': 102
  }

def subscribe_ticker_msg(market):
  return {
    'op': 'subscribe', 
    'tag': 1,
    'args': [f'ticker:{market}']
  }

def subscribe_depth_msg(market):
  return {
    "op": "subscribe",
    "tag": 103,
    "args": [f"depth:{market}"]
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

def get_best_buyPrice_and_sellPrice(depth_data, diff):
  sell_list = depth_data['asks']
  best_sell_price = None
  cumulate_amount = 0
  for i in range(len(sell_list)):
    cumulate_amount += sell_list[i][1]
    if cumulate_amount > diff:
      if i-1 >=0:
        best_sell_price = sell_list[i-1][0]
      else:
        best_sell_price = sell_list[0][0]
      break
  if (best_sell_price == None): best_sell_price = sell_list[-1][0]

  buy_list = depth_data['bids']
  best_buy_price = None
  cumulate_amount = 0
  for i in range(len(buy_list)):
    cumulate_amount += buy_list[i][1]
    if cumulate_amount > diff:
      if i-1 >=0:
        best_buy_price = buy_list[i-1][0]
      else:
        best_buy_price = buy_list[0][0]
      break
  if (best_buy_price == None): best_buy_price = buy_list[-1][0]
  
  return best_buy_price, best_sell_price

async def initial_conn(ws):
  await ws.send(json.dumps(auth_msg()))
  await ws.send(json.dumps(subscribe_orders_msg('FLEX-USD')))
  await ws.send((json.dumps(subscribe_depth_msg('FLEX-USD'))))
  # await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'BUY', 1, 4.5)))

async def process():
  async with websockets.connect(websocket_endpoint) as ws:
    global buy_price
    global sell_price
    await initial_conn(ws)
    while ws.open:
      resp = await ws.recv()
      msg = json.loads(resp)
      # print(msg)
      if 'event' in msg and msg['event']=='login':
        ts = msg['timestamp']
        print(f'{TERM_GREEN}Login succeed at {datetime.fromtimestamp(int(ts) / 1000)}{TERM_NFMT}\n')
      if 'table' in msg and msg['table']=='depth':
        depth_data = msg['data'][0]
        new_buy_price, new_sell_price = get_best_buyPrice_and_sellPrice(depth_data, depth_amount)
        if buy_price != new_buy_price or sell_price != new_sell_price:
          print(f'{TERM_GREEN}update buy_price: {buy_price} => {new_buy_price}, {sell_price} => {new_sell_price}{TERM_NFMT}')
          buy_price = new_buy_price
          sell_price = new_sell_price
      if 'table' in msg and msg['table']=='order':
        data = msg['data'][0]
        print(f'{TERM_BLUE}{data}{TERM_NFMT}')
        if 'notice' in data and data['notice'] == 'OrderMatched':
          side = data['side']
          quantity = float(data['matchQuantity'])
          price = float(data['price'])
          if side == 'BUY':
            # 买单成交了,要挂卖单
            print(f'{TERM_GREEN}Execute sell order: {quantity} - {sell_price}{TERM_NFMT}')
            await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'SELL', quantity, sell_price)))
          elif side == 'SELL':
            # 卖单成交了,要挂买单
            print(f'{TERM_GREEN}Execute bull order: {round(quantity * price / buy_price, 1)} - {buy_price}{TERM_NFMT}')
            await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'BUY', round(quantity * price / buy_price, 1), buy_price)))

if __name__ == '__main__':
  print(f'{TERM_GREEN}Config loaded, user: {user_id}, buy_price: {buy_price}, sell_price: {sell_price}{TERM_NFMT}')
  try:
    asyncio.get_event_loop().run_until_complete(process())
  except Exception as err:
    print(err)
    print(f'{TERM_RED}Errors, try to reconnect...{TERM_NFMT}')
    asyncio.get_event_loop().run_until_complete(process())