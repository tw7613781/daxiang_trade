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
from urllib.parse import urlencode

import requests
from src.websocket_app import MyWebSocketApp
from src.common.global_utils import *

class CoinflexBase():

  def __init__(self, config_file):    
    self.exchange = "CoinFLEX"
    self.init_finish_event = threading.Event()  # 用来控制服务初始化完成才处理请求

    self.con_file = config_file

    self.ws_url = get_json_config(file=self.con_file, section=self.exchange, key="WSURL")
    self.account_id = get_json_config(file=self.con_file, section=self.exchange, key="USERID")
    self.api_key = get_json_config(file=self.con_file, section=self.exchange, key="APIKEY")
    self.secret_key = get_json_config(file=self.con_file, section=self.exchange, key="APISECRET")
    
    self.market = get_json_config(file=self.con_file, section=self.exchange, key="MARKET")

    self.http_host = get_json_config(file=self.con_file, section=self.exchange, key="HTTPURL")
    self.http_path = get_json_config(file=self.con_file, section=self.exchange, key="HTTPPATH")
    self.nonce = get_json_config(file=self.con_file, section=self.exchange, key="NONCE")
  
    self.ping_interval = 10
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + current_time_string(), log_path="./logs")

    self.websocket_app = MyWebSocketApp(self)
    
    self.init_finish_event.set()

  def on_message(self, msg, ws=None):
    """
    处理websocket的market数据
    :param msg:
    :return:
    """
    try:
      msg = json.loads(msg)
      self.logger.info(msg)

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
  
  def place_limit_order_msg(self, market, side, quantity, price, recv_window = 1000):
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
        'price': float(price),
        "recvWindow": float(recv_window)
      }
    }
    return json.dumps(msg)
  
  def modify_limit_order_msg(self, market, order_id, new_quantity, new_price, recv_window = 1000):
    msg = {
      "op": "modifyorder",
      "tag": 1,
      "data": {
        "timestamp": current_milli_ts(),
        "marketCode": market,
        "orderId": order_id,
        "price": float(new_price),
        "quantity": float(new_quantity),
        "recvWindow": float(recv_window)
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
      for currency in data:
        if currency["instrumentId"] == "USD":
          available_balance = currency["available"]
      return available_balance
    except:
      self.logger.error("get available USD balance Error!!!")
      self.logger.error(traceback.format_exc())