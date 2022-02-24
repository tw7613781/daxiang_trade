# -*- coding: utf-8 -*-
# @Time    : 2022/2/11 21:42
# @Author  : tw7613781
# @Site    : 
# @File    : coinflex.py
# @Software: vscode

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
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + self.strategyName + "_" + current_time_string(), log_path="./logs")
    self.logger.info(f'{TERM_GREEN}Config loaded ==> user: {self.account_id}, buy_price: {self.buy_price}, sell_price: {self.sell_price}{TERM_NFMT}')

    self.orders = []
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
            self.websocket_app.send_command(self.place_limit_order_msg(self.market, 'SELL',  data['matchQuantity'], self.sell_price))
            self.logger.info(f'{TERM_GREEN}Execute sell order: {self.sell_price} - {data["matchQuantity"]}{TERM_NFMT}')
          elif data['side'] == 'SELL':
            # 卖单成交了,要挂买单
            usd_available = self.get_available_USD_balance()
            new_quantity = str(math.floor(Decimal(usd_available) / Decimal(self.buy_price) * 10) / 10)
            if (Decimal(new_quantity) > 0):
              self.websocket_app.send_command(self.place_limit_order_msg(self.market, "BUY", new_quantity, self.buy_price))
              self.logger.info(f'{TERM_GREEN}Execute buy order: {self.buy_price} - {new_quantity}{TERM_NFMT}')
            
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