import websockets
import asyncio
import hmac
import base64
import hashlib
import json
import os
import math
from datetime import datetime
from dotenv import load_dotenv
from utils import current_milli_ts, TERM_BLUE, TERM_NFMT, TERM_GREEN, TERM_RED

from global_utils import *

load_dotenv()

api_key = os.getenv('APIKEY')
api_secret = os.getenv('APISECRET')
user_id = os.getenv('USERID')

sell_price = float(os.getenv('SELLPRICE'))
buy_price = float(os.getenv('BUYPRICE'))
depth_amount = float(os.getenv('DEPTHAMOUNT'))

websocket_endpoint = 'wss://v2api.coinflex.com/v2/websocket'

logger = setup_logger(__file__)

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

def get_best_price(depth_data, diff):
  best_price = None
  accumulated_amount = 0
  for i in range(len(depth_data)):
    accumulated_amount += depth_data[i][1]
    if accumulated_amount > diff:
      if i-1 >=0:
        best_price = depth_data[i-1][0]
      break

  return best_price

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
        logger.info(f'{TERM_GREEN}Login succeed{TERM_NFMT}')
      if 'table' in msg and msg['table']=='depth':
        depth_data = msg['data'][0]
        new_buy_price = get_best_price(depth_data['bids'], depth_amount)
        new_sell_price = get_best_price(depth_data['asks'], depth_amount)
        if (new_buy_price != None and new_buy_price != buy_price):
          logger.info(f'{TERM_GREEN}Update buy_price: {buy_price} => {new_buy_price}, {sell_price} => {new_sell_price}{TERM_NFMT}')
          buy_price = new_buy_price
        if (new_sell_price != None and new_sell_price != sell_price):
          logger.info(f'{TERM_GREEN}Update sell_price: {buy_price} => {new_buy_price}, {sell_price} => {new_sell_price}{TERM_NFMT}')
          sell_price = new_sell_price
      if 'table' in msg and msg['table']=='order':
        data = msg['data'][0]
        logger.info(f'{TERM_BLUE}{data}{TERM_NFMT}')
        if 'notice' in data and data['notice'] == 'OrderMatched':
          side = data['side']
          quantity = float(data['matchQuantity'])
          price = float(data['price'])
          if side == 'BUY':
            # 买单成交了,要挂卖单
            logger.info(f'{TERM_GREEN}Execute sell order: {quantity} - {sell_price}{TERM_NFMT}')
            await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'SELL', quantity, sell_price)))
          elif side == 'SELL':
            # 卖单成交了,要挂买单
            logger.info(f'{TERM_GREEN}Execute bull order: {math.floor(quantity * price / buy_price)} - {buy_price}{TERM_NFMT}')
            await ws.send(json.dumps(place_limit_order_msg('FLEX-USD', 'BUY', math.floor(quantity * price / buy_price), buy_price)))


if __name__ == '__main__':
  logger.info(f'{TERM_GREEN}Config loaded, user: {user_id}, buy_price: {buy_price}, sell_price: {sell_price}{TERM_NFMT}')

  while True:
    try:
      loop = asyncio.get_event_loop()
      loop.run_until_complete(process())
      loop.close()
    except Exception as err:
      logger.error(f"{TERM_RED}Caught exception: {err}{TERM_NFMT}")
