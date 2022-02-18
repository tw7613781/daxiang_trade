# -*- coding: utf-8 -*-
# @Time    : 2022/2/11 21:42
# @Author  : tw7613781
# @Site    : 
# @File    : coinflex.py
# @Software: vscode

import threading
import hmac
import base64
import hashlib
import math
import time
from decimal import Decimal
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

    self.buy_price = str(get_json_config(file=self.con_file, section=self.exchange, key="BUYPRICE"))
    self.sell_price = str(get_json_config(file=self.con_file, section=self.exchange, key="SELLPRICE"))
    self.buy_volume = str(get_json_config(file=self.con_file, section=self.exchange, key="BUYVOLUME"))
    self.sell_volume = str(get_json_config(file=self.con_file, section=self.exchange, key="SELLVOLUME"))
    self.min_price_step = str(get_json_config(file=self.con_file, section=self.exchange, key="MINPRICESTEP"))

    self.price_update_interval = int(get_json_config(file=self.con_file, section=self.exchange, key="PRICEUPDATEINTERVAL"))
    
    self.http_host = get_json_config(file=self.con_file, section=self.exchange, key="HTTPURL")
    self.http_path = get_json_config(file=self.con_file, section=self.exchange, key="HTTPPATH")
    self.nonce = get_json_config(file=self.con_file, section=self.exchange, key="NONCE")
  
    self.ping_interval = 10
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + current_time_string(), log_path="./logs")
    self.logger.info(f'{TERM_GREEN}Config loaded ==> user: {self.account_id}, buy_price: {self.buy_price}, sell_price: {self.sell_price}, buy_volume: {self.buy_volume}, sell_volume: {self.sell_volume}, price_update_interval: {self.price_update_interval}{TERM_NFMT}')

    self.websocket_app = MyWebSocketApp(self)

    self.orders = []
    self.last_buy_price_updated_ts = 0
    self.last_sell_price_updated_ts = 0

    self.usd_balance = "0"
    
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
        new_buy_price, new_sell_price = self.get_best_price(depth_data, self.buy_volume, self.sell_volume, self.min_price_step)
        cur_ts = int(current_milli_ts())
        
        # 更新buy_price
        if Decimal(new_buy_price) != Decimal(self.buy_price):
          self.logger.info(f'Update buy_price: {self.buy_price} => {new_buy_price}, {self.sell_price}')
          self.buy_price = new_buy_price
        
          # 如果更新周期到了,更新orders
          if (cur_ts - self.last_buy_price_updated_ts) > self.price_update_interval:
            self.last_buy_price_updated_ts = int(current_milli_ts())
            for order in self.get_buy_orders():
              ## 更新buy_order不太一样,需要看自己有多少usd,才能决定以新的价格能买多少
              ## 拿到account available USD, 用available_usd除以self.buy_price得到应该下单的volume
              usd_available = self.get_available_USD_balance()
              new_quantity = str(math.floor(Decimal(usd_available) / Decimal(self.buy_price) * 10) / 10)
              if (Decimal(new_quantity) > 0):
                self.websocket_app.send_command(self.modify_limit_order_msg(self.market, "BUY", new_quantity, self.buy_price))

        # 更新sell_price
        if Decimal(new_sell_price) != Decimal(self.sell_price):
          self.logger.info(f'Update sell_price: {self.buy_price}, {self.sell_price} => {new_sell_price}')
          self.sell_price = new_sell_price
        
          if (cur_ts - self.last_sell_price_updated_ts) > self.price_update_interval:
            self.last_sell_price_updated_ts = int(current_milli_ts())
            for order in self.get_sell_orders():
              # 直接更新sell order的价格
              quantity = order["remainQuantity"] if order["remainQuantity"] else order["quantity"]
              self.websocket_app.send_command(self.modify_limit_order_msg(self.market, order["orderId"], quantity, self.sell_price))
      
      if 'table' in msg and msg['table']=='order':
        data = msg['data'][0]
        # self.logger.info(f'{TERM_BLUE}{data}{TERM_NFMT}')
        if 'notice' in data and data['notice'] == 'OrderOpened':
          # 开单,把order加入self.orders列表
          self.orders.append(data)
          self.logger.info(f'{TERM_BLUE}Update order list, add order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} {TERM_NFMT}')
          self.display_orders()

        if 'notice' in data and data['notice'] == 'OrderClosed':
          # 关闭单,把order从self.orders列表删除
          for index, order in enumerate(self.orders):
            if order['orderId'] == data['orderId']:
              del self.orders[index]
              break
          self.logger.info(f'{TERM_BLUE}Update order list, remove order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} - {data["status"]} {TERM_NFMT}')
          self.display_orders()

        if 'notice' in data and data['notice'] == 'OrderModified':
          # 修改单,把原order从self.orders列表删除,然后把此order添加进orders列表
          for index, order in enumerate(self.orders):
            if order['orderId'] == data['orderId']:
              del self.orders[index]
              break
          self.orders.append(data)
          self.logger.info(f'{TERM_BLUE}Update order list, modified order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} - {data["status"]} {TERM_NFMT}')
          self.display_orders()
              

        if 'notice' in data and data['notice'] == 'OrderMatched':

          ## 如果是部分成交,关掉此成交单,从orders列表中删除,再把剩余volume建一个新单
          ## 如果是全部成交,就删除就好了
          # 把此order从self.orders列表删除
          for index, order in enumerate(self.orders):
            if order['orderId'] == data['orderId']:
              del self.orders[index]
              break
          if Decimal(data["remainQuantity"]) != Decimal("0"):
            self.websocket_app.send_command(self.cancel_limit_order_msg(self.market, data["orderId"]))
            time.sleep(1)
            if data['side'] == "BUY":
              usd_available = self.get_available_USD_balance()
              new_quantity = str(math.floor(Decimal(usd_available) / Decimal(data['matchPrice']) * 10) / 10)
              if (Decimal(new_quantity) > 0):
                self.websocket_app.send_command(self.place_limit_order_msg(self.market, "BUY", new_quantity, data['matchPrice']))
            if data['side'] == "SELL":
              self.websocket_app.send_command(self.place_limit_order_msg(self.market, "SELL", data['remainQuantity'], data['matchPrice']))
          
          self.logger.info(f'{TERM_BLUE}Update order list, remove order: {data["orderId"]} - {data["side"]} - {(data["price"])} - {data["matchQuantity"]} - THE ORDER IS FULLY FILLED OR PARTIALLY FILLED {TERM_NFMT}')
          self.display_orders()

          if data['side'] == 'BUY':
            # 买单成交了,要挂卖单
            self.logger.info(f'{TERM_RED}Execute sell order: { data["matchQuantity"]} - {self.sell_price}{TERM_NFMT}')
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, 'SELL',  data['matchQuantity'], self.sell_price))
          elif data['side'] == 'SELL':
            # 卖单成交了,要挂买单
            usd_available = self.get_available_USD_balance()
            new_quantity = str(math.floor(Decimal(usd_available) / Decimal(self.buy_price) * 10) / 10)
            if (Decimal(new_quantity) > 0):
              self.websocket_app.send_command(self.place_limit_order_msg(self.market, "BUY", new_quantity, self.buy_price))
              self.logger.info(f'{TERM_RED}Execute bull order: {new_quantity} - {self.buy_price}{TERM_NFMT}')
            
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
        self.display_orders()
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
        'quantity': float(quantity),
        'price': float(price)
      }
    }
    return json.dumps(msg)
  
  def modify_limit_order_msg(self, market, order_id, new_quantity, new_price):
    msg = {
      "op": "modifyorder",
      "tag": 1,
      "data": {
        "timestamp": current_milli_ts(),
        "marketCode": market,
        "orderId": order_id,
        "price": float(new_price),
        "quantity": float(new_quantity)
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

  def get_best_price(self, depth_data, buy_volume, sell_volume, min_price_step):
    buy_order_table = depth_data["bids"]
    buy_orders = self.get_buy_orders()
  
    sell_order_table = depth_data["asks"]
    sell_orders = self.get_sell_orders()

    # buy price
    buy_price = None
    buy_accumulated_volume = Decimal("0")
    for order in buy_order_table:
      buy_accumulated_volume += Decimal(str(order[1]))
      for my_buy_order in buy_orders:
        if Decimal(str(my_buy_order["price"])) == Decimal(str(order[0])):
           buy_accumulated_volume -= Decimal(str(my_buy_order["quantity"]))
      if buy_accumulated_volume >= Decimal(buy_volume):
        buy_price = str(order[0])
        break
    if buy_price == None:
      buy_price = str(buy_order_table[-1][0])
    if Decimal(add(buy_price, min_price_step)) < Decimal(str(sell_order_table[0][0])):
      buy_price = add(buy_price, min_price_step)

    # sell price
    sell_price = None
    sell_accumulated_volume = Decimal("0")
    for order in sell_order_table:
      sell_accumulated_volume += Decimal(str(order[1]))
      for my_sell_order in sell_orders:
        if Decimal(str(my_sell_order["price"])) == Decimal(str(order[0])):
           sell_accumulated_volume -= Decimal(str(my_sell_order["quantity"]))   
      if sell_accumulated_volume >= Decimal(sell_volume):
        sell_price = str(order[0])
        break
    if sell_price == None:
      sell_price = str(sell_order_table[-1][0])
    if Decimal(sub(sell_price, min_price_step)) > Decimal(str(buy_order_table[0][0])):
      sell_price = sub(sell_price, min_price_step)

    return buy_price, sell_price

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
      endpoint = '/v2.1/orders'
      return(self.private_http_call(endpoint))
    except:
      self.logger.error("http getOrders Error!!!")
      self.logger.error(traceback.format_exc())

  def getBalance(self):
    '''
    get account balance
    '''
    try:
      endpoint = '/v2/balances'
      return(self.private_http_call(endpoint))
    except:
      self.logger.error("http getBalance Error!!!")
      self.logger.error(traceback.format_exc())
  
  def get_available_USD_balance(self):
    try:
      data = self.getBalance()["data"]
      available_balance = "0"
      self.logger.info(data)
      for currency in data:
        if currency["instrumentId"] == "USD":
          available_balance = currency["available"]
      return available_balance
    except:
      self.logger.error("get available USD balance Error!!!")
      self.logger.error(traceback.format_exc())  
  
  def display_orders(self):
    for order in self.orders:
      self.logger.warn(f'Order: {order["orderId"]} - {order["side"]} - {order["quantity"]} - {order["price"]}')
  
  def get_buy_orders(self):
    return list(filter(lambda order: order["side"] == "BUY", self.orders))
  
  def get_sell_orders(self):
    return list(filter(lambda order: order["side"] == "SELL", self.orders))

  