# -*- coding: utf-8 -*-
# @Time    : 2022/2/11 21:42
# @Author  : tw7613781
# @Site    : 
# @File    : coinflex.py
# @Software: vscode

from curses import termattrs
import threading
import hmac
import base64
import hashlib
import math
from urllib.parse import urlencode

import requests
from src.websocket_app import MyWebSocketApp
from src.common.global_utils import *

class Coinflex():

  def __init__(self, config_file):    
    self.exchange = "CoinFLEX"
    self.init_finish_event = threading.Event()  # 用来控制服务初始化完成才处理请求

    self.con_file = config_file

    self.ws_url = get_json_config(file=self.con_file, section=self.exchange, key="WSURL")
    self.account_id = get_json_config(file=self.con_file, section=self.exchange, key="USERID")
    self.api_key = get_json_config(file=self.con_file, section=self.exchange, key="APIKEY")
    self.secret_key = get_json_config(file=self.con_file, section=self.exchange, key="APISECRET")
    
    self.market = get_json_config(file=self.con_file, section=self.exchange, key="MARKET")
    self.buy_price = float(get_json_config(file=self.con_file, section=self.exchange, key="BUYPRICE"))
    self.sell_price = float(get_json_config(file=self.con_file, section=self.exchange, key="SELLPRICE"))
    self.volume = float(get_json_config(file=self.con_file, section=self.exchange, key="VOLUME"))
    self.price_update_interval = float(get_json_config(file=self.con_file, section=self.exchange, key="PRICEUPDATEINTERVAL"))

    self.http_host = get_json_config(file=self.con_file, section=self.exchange, key="HTTPURL")
    self.http_path = get_json_config(file=self.con_file, section=self.exchange, key="HTTPPATH")
    self.nonce = get_json_config(file=self.con_file, section=self.exchange, key="NONCE")
  
    self.ping_interval = 10
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + current_time_string(), log_path="./logs")
    self.logger.info(f'{TERM_GREEN}Config loaded ==> user: {self.account_id}, buy_price: {self.buy_price}, sell_price: {self.sell_price}, volume: {self.volume}{TERM_NFMT}')

    self.websocket_app = MyWebSocketApp(self)

    self.orders = []
    self.last_updated_ts = 0
    
    self.init_finish_event.set()

  def on_message(self, msg, ws=None):
    """
    处理websocket的market数据
    :param msg:
    :return:
    """
    try:
      msg = json.loads(msg)

      if 'event' in msg and msg['event']=='login':
        self.logger.info(f'{TERM_GREEN}Login succeed{TERM_NFMT}')
      
      if 'table' in msg and msg['table']=='depth':
        depth_data = msg['data'][0]
        new_buy_price = self.get_best_price(depth_data['bids'], self.volume)
        new_sell_price = self.get_best_price(depth_data['asks'], self.volume)
        cur_ts = int(current_milli_ts())
        
        # get new buy price, update buy price if the buy order is hung for certain time
        if (new_buy_price != None and (cur_ts - self.last_updated_ts) / 1000 > self.price_update_interval):
          if new_buy_price != self.buy_price:
            self.logger.info(f'{TERM_GREEN}Update buy_price: {self.buy_price} => {new_buy_price}, {self.sell_price}{TERM_NFMT}')
            self.buy_price = new_buy_price
          for order in self.orders:
            if order["side"] == "BUY" and float(order["price"]) != self.buy_price:
              self.websocket_app.send_command(self.modify_limit_order_msg(self.market, order["orderId"], self.buy_price))
          self.last_updated_ts = int(current_milli_ts())

        # get new sell price, update sell price if the sell order is hung for certain time  
        if (new_sell_price != None and (cur_ts - self.last_updated_ts) / 1000 > self.price_update_interval):
          if new_sell_price != self.sell_price:
            self.logger.info(f'{TERM_GREEN}Update sell_price: {self.buy_price}, {self.sell_price} => {new_sell_price}{TERM_NFMT}')
            self.sell_price = new_sell_price
          for order in self.orders:
            if order["side"] == "SELL" and float(order["price"] != self.sell_price):
              self.websocket_app.send_command(self.modify_limit_order_msg(self.market, order["orderId"], self.sell_price))
          self.last_updated_ts = int(current_milli_ts())
      
      if 'table' in msg and msg['table']=='order':
        data = msg['data'][0]
        self.logger.info(f'{TERM_BLUE}{data}{TERM_NFMT}')
        if 'notice' in data and data['notice'] == 'OrderOpened':
          # 开单,把order加入self.orders列表
          self.orders.append(data)
          self.logger.info(f'{TERM_BLUE}Update order list, add order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} {TERM_NFMT}')
          self.logger.info(self.orders)

        if 'notice' in data and data['notice'] == 'OrderClosed':
          # 关闭单,把order从self.orders列表删除
          for index in range(len(self.orders)):
            if self.orders[index]['orderId'] == data['orderId']:
              del self.orders[index]
              self.logger.info(f'{TERM_BLUE}Update order list, remove order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} - {data["status"]} {TERM_NFMT}')
              self.logger.info(self.orders)
              break

        if 'notice' in data and data['notice'] == 'OrderModified':
          # 修改单,把原order从self.orders列表删除,然后把此order添加进orders列表
          for index in range(len(self.orders)):
            if self.orders[index]['orderId'] == data['orderId']:
              del self.orders[index]
              self.orders.append(data)
              self.logger.info(f'{TERM_BLUE}Update order list, modified order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} - {data["status"]} {TERM_NFMT}')
              self.logger.info(self.orders)
              break
              

        if 'notice' in data and data['notice'] == 'OrderMatched':
          side = data['side']
          quantity = float(data['matchQuantity'])
          price = float(data['matchPrice'])

          ## 如果是部分成交,关掉此成交单,从orders列表中删除,再把剩余volume建一个新单
          ## 如果是全部成交,就删除就好了
          # 把此order从self.orders列表删除
          for index in range(len(self.orders)):
            if self.orders[index]['orderId'] == data['orderId']:
              del self.orders[index]
              if data["remainQuantity"] != "0":
                self.websocket_app.send_command(self.cancel_limit_order_msg(self.market, data["orderId"]))
                self.websocket_app.send_command(self.place_limit_order_msg(self.market, data["side"], data["remainQuantity"], data["price"]))
              self.logger.info(f'{TERM_BLUE}Update order list, remove order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} - THE ORDER IS FULLY FILLED OR PARTIALLY FILLED {TERM_NFMT}')
              self.logger.info(self.orders)
              break

          if side == 'BUY':
            # 买单成交了,要挂卖单
            self.logger.info(f'{TERM_GREEN}Execute sell order: {quantity} - {self.sell_price}{TERM_NFMT}')
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, 'SELL', quantity, self.sell_price))
          elif side == 'SELL':
            # 卖单成交了,要挂买单
            self.logger.info(f'{TERM_GREEN}Execute bull order: {math.floor(quantity * price / self.buy_price * 10) / 10} - {self.buy_price}{TERM_NFMT}')
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, 'BUY', math.floor(quantity * price / self.buy_price * 10) / 10, self.buy_price))
            
    except:
      self.logger.error("on_message error!  %s " % msg)
      self.logger.error(traceback.format_exc())

  def on_error(self, error):
    """ Called on fatal websocket errors. We exit on these. """
    try:
      self.logger.error("%s __on_error : %s", self.exchange, error)
    except:
      self.logger.error("on_error Error!!!")
      self.logger.error(traceback.format_exc())

  def on_open(self):
    """ Called when the WS opens. """
    try:
      self.logger.info("%s websocket opened.", self.exchange)
      ## send auth msg and subscribe msgs
      self.websocket_app.send_command(self.auth_msg())
      self.websocket_app.send_command(self.subscribe_orders_msg(self.market))
      self.websocket_app.send_command(self.subscribe_depth_msg(self.market))
      msg = self.getOrders()
      if 'event' in msg and msg['event']=='orders' and msg['data']:
        self.orders = msg['data']
        self.logger.info(self.orders)
    except:
      self.logger.error("on_open Error!!!")
      self.logger.error(traceback.format_exc())

  def on_close(self):
    """ Called on websocket close."""
    try:
      self.logger.info("%s websocket closed.", self.exchange)
    except:
      self.logger.error("on_close Error!!!")
      self.logger.error(traceback.format_exc())

  def auth_msg(self):
    ts = current_milli_ts()
    sig_payload = (ts + 'GET/auth/self/verify').encode('utf-8')
    signature = base64.b64encode(hmac.new(self.secret_key.encode('utf-8'), sig_payload, hashlib.sha256).digest()).decode('utf-8')
    msg = {
      'op': 'login',
      'tag': 1,
      'data': {
        'apiKey': self.api_key,
        'timestamp': ts,
        'signature': signature
        }
    }
    return json.dumps(msg)
  
  def subscribe_balance_msg(self):
    msg = {
      'op': 'subscribe',
      'args': ['balance:all'],
      'tag': 101
    }
    return json.dumps(msg)
  
  def subscribe_orders_msg(self, market):
    msg = {
      'op': 'subscribe', 
      'args': [f'order:{market}'], 
      'tag': 102
    }
    return json.dumps(msg)

  def subscribe_ticker_msg(self, market):
    msg = {
      'op': 'subscribe', 
      'tag': 1,
      'args': [f'ticker:{market}']
    }
    return json.dumps(msg)

  def subscribe_depth_msg(self, market):
    msg = {
      "op": "subscribe",
      "tag": 103,
      "args": [f"depth:{market}"]
    }
    return json.dumps(msg)
  
  def place_limit_order_msg(self, market, side, quantity, price):
    msg = {
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
    return json.dumps(msg)
  
  def modify_limit_order_msg(self, market, order_id, new_price):
    msg = {
      "op": "modifyorder",
      "tag": 1,
      "data": {
        "timestamp": current_milli_ts(),
        "marketCode": market,
        "orderId": order_id,
        "price": new_price,
      }
    }
    return json.dumps(msg)
  
  def cancel_limit_order_msg(self, market, order_id):
    msg = {
      "op": "cancelorder",
      "tag": 456,
      "data": {
        "marketCode": market,
        "orderId": order_id
      }
    }
    return json.dumps(msg)

  def get_best_price(self, depth_data, diff):
    best_price = None
    accumulated_amount = 0
    for i in range(len(depth_data)):
      accumulated_amount += depth_data[i][1]
      if accumulated_amount > diff:
        if i-1 >=0:
          best_price = depth_data[i-1][0]
        break

    return best_price

  def private_http_call(self, method, options={}, action='GET'):
    '''
    generate header based on api credential
    method: private call method
    options: parameters if have,, the format is as below
          {'key1': 'value1', 'key2': 'value2'}
    '''
    ts = datetime.datetime.utcnow().isoformat()
    body = urlencode(options)
    if options:
      path = method + '?' + body
    else:
      path = method
    msg_string = '{}\n{}\n{}\n{}\n{}\n{}'.format(ts, self.nonce, action, self.http_path, method, body)
    sig = base64.b64encode(hmac.new(self.secret_key.encode('utf-8'), msg_string.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')

    header = {'Content-Type': 'application/json', 'AccessKey': self.api_key,
              'Timestamp': ts, 'Signature': sig, 'Nonce': str(self.nonce)}

    if action == 'GET': 
      resp = requests.get(self.http_host + path, headers=header)
    elif action == 'POST':
      resp = requests.post(self.http_host + path, headers=header)
    return resp.json()

  def getOrders(self):
    '''
    get account's unfilled orders
    '''
    try:
      endpoint = '/v2/orders'
      return(self.private_http_call(endpoint))
    except:
      self.logger.error("http getOrders Error!!!")
      self.logger.error(traceback.format_exc())