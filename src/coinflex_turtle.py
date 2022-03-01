# -*- coding: utf-8 -*-
# @Time    : 2022/2/11 21:42
# @Author  : tw7613781
# @Site    : 
# @File    : coinflex.py
# @Software: vscode

from ast import In
import math
from decimal import Decimal

from src.common.global_utils import *
from src.coinflex_base import CoinflexBase

class CoinflexTurtle(CoinflexBase):

  def __init__(self, config_file):    
    super(CoinflexTurtle, self).__init__(config_file)

    self.strategyName = "Turtle"

    self.buy_price = str(get_json_config(file=self.con_file, section=self.exchange, key="BUYPRICE"))
    self.sell_price = str(get_json_config(file=self.con_file, section=self.exchange, key="SELLPRICE"))
    self.middle_price = str(get_json_config(file=self.con_file, section=self.exchange, key="MIDDLEPRICE"))
    self.steps = str(get_json_config(file=self.con_file, section=self.exchange, key="STEPS"))
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + self.strategyName + "_" + current_time_string(), log_path="./logs")
    self.logger.info(f'{TERM_GREEN}Config loaded ==> user: {self.account_id}, buy_price: {self.buy_price}, middle_price: {self.middle_price}, sell_price: {self.sell_price}, steps: {self.steps}{TERM_NFMT}')

    self.orders = []
    self.sell_step = None
    self.buy_step = None
    self.recv_window = 1000
    
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

      if 'event' in msg and msg['event']=='placeorder':
        order_succeed = msg['submitted'] if 'submitted' in msg else False
        if not order_succeed:
          self.logger.error(msg)
          data = msg['data']
          if "recvWindow" in msg["message"]:
            self.recv_window +=500
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, data["side"], data["quantity"], data["price"], self.recv_window))
          elif "FAILED balance check" in msg["message"]:
            quantity = Decimal(str(data['quantity'])) - Decimal("0.1")
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, data["side"], quantity, data["price"]))

      if 'table' in msg and msg['table']=='depth':
        depth_data = msg['data'][0]
        new_buy_price, new_sell_price = self.get_best_price(depth_data)
        # self.logger.info(f'{new_buy_price} - {new_sell_price}')

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

          self.logger.info(f'{TERM_RED}Order matched: {data["orderId"]} - {data["side"]} - {(data["price"])} - {data["matchQuantity"]}{TERM_NFMT}')

          if Decimal(data["remainQuantity"]) == Decimal("0"):
            for index, order in enumerate(self.orders):
              if order['orderId'] == data['orderId']:
                self.logger.info(f'{TERM_BLUE}Update order list, remove order: {data["orderId"]} - {data["side"]} - {data["price"]} - {data["quantity"]} - {data["status"]} {TERM_NFMT}')
                del self.orders[index]
                break

          if data['side'] == 'BUY':
            # 买单成交了,要挂卖单
            price = data['price']
            steps = (Decimal(self.middle_price) - Decimal(str(price))) / Decimal(self.buy_step)
            price = Decimal(str(self.middle_price)) + steps * Decimal(self.sell_step)
            format_price = str(math.floor(price * 1000) / 1000)
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, 'SELL',  data['matchQuantity'], format_price))
            self.logger.info(f'{TERM_GREEN}Execute sell order: {format_price} - {data["matchQuantity"]}{TERM_NFMT}')
          elif data['side'] == 'SELL':
            # 卖单成交了,要挂买单
            price = data['price']
            steps = (Decimal(str(price)) - Decimal(self.middle_price)) / Decimal(self.sell_step)
            price = Decimal(str(self.middle_price)) - steps * Decimal(self.buy_step)
            format_price = str(math.floor(price * 1000) / 1000)

            usd_available = Decimal(str(data['price'])) * Decimal(str(data['matchQuantity']))
            new_quantity = str(math.floor(Decimal(usd_available) / Decimal(format_price) * 10) / 10)
            if (Decimal(new_quantity) > 0):
              self.websocket_app.send_command(self.place_limit_order_msg(self.market, "BUY", new_quantity, format_price))
              self.logger.info(f'{TERM_GREEN}Execute buy order: {format_price} - {new_quantity}{TERM_NFMT}')
            
    except:
      self.logger.error("on_message error!  %s " % msg)
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
      self.initial_orders()
    except:
      self.logger.error("on_open Error!!!")
      self.logger.error(traceback.format_exc())

  def get_best_price(self, depth_data):
    buy_order_table = depth_data["bids"]
    buy_price = buy_order_table[0][0]

    sell_order_table = depth_data["asks"]
    sell_price = sell_order_table[0][0]

    return buy_price, sell_price

  def display_orders(self):
    for order in self.orders:
      self.logger.warn(f'Order: {order["orderId"]} - {order["side"]} - {order["price"]} - {order["quantity"]}')
  
  def get_buy_orders(self):
    return list(filter(lambda order: order["side"] == "BUY", self.orders))
  
  def get_sell_orders(self):
    return list(filter(lambda order: order["side"] == "SELL", self.orders))

  def initial_orders(self):
    tokens = self.market.split('-')
    
    sell_token = tokens[0]
    sell_balance = str(self.get_available_balance_by_id(sell_token))
    sell_amount = str(math.floor( Decimal(sell_balance) / Decimal(self.steps) * 10) / 10)
    self.sell_step = (Decimal(self.sell_price) - Decimal(self.middle_price)) / Decimal(self.steps)
    if (Decimal(sell_amount) > 0):
      price = self.middle_price
      for i in range(int(self.steps)):
        price = Decimal(price) + Decimal(self.sell_step)
        format_price = str(math.floor(price * 1000) / 1000)
        self.websocket_app.send_command(self.place_limit_order_msg(self.market, "SELL", sell_amount, format_price))
        self.logger.info(f'{TERM_GREEN}Execute sell order: {format_price} - {sell_amount}{TERM_NFMT}')
    
    buy_token = tokens[1]
    buy_balance = self.get_available_balance_by_id(buy_token)
    buy_amount = str(math.floor(Decimal(buy_balance) / Decimal(self.steps) * 10) / 10) 
    self.buy_step = (Decimal(self.middle_price) - Decimal(self.buy_price)) / Decimal(self.steps)
    price = self.middle_price
    for i in range(int(self.steps)):
      price = Decimal(price) - Decimal(self.buy_step)
      format_price = str(math.floor(price * 1000) / 1000)
      amount = str(math.floor(Decimal(buy_amount) / Decimal(format_price) * 10) / 10)
      if (Decimal(amount) > 0):
        self.websocket_app.send_command(self.place_limit_order_msg(self.market, "BUY", amount, format_price))
        self.logger.info(f'{TERM_GREEN}Execute buy order: {format_price} - {amount}{TERM_NFMT}')
