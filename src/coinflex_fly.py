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

class CoinflexFly(CoinflexBase):

  def __init__(self, config_file):    
    super(CoinflexFly, self).__init__(config_file)

    self.strategyName = "Fly"

    self.buy_price = str(get_json_config(file=self.con_file, section=self.exchange, key="BUYPRICE"))
    self.sell_price = str(get_json_config(file=self.con_file, section=self.exchange, key="SELLPRICE"))
    self.buy_volume = str(get_json_config(file=self.con_file, section=self.exchange, key="BUYVOLUME"))
    self.sell_volume = str(get_json_config(file=self.con_file, section=self.exchange, key="SELLVOLUME"))
    self.min_price_step = str(get_json_config(file=self.con_file, section=self.exchange, key="MINPRICESTEP"))

    self.price_update_interval = int(get_json_config(file=self.con_file, section=self.exchange, key="PRICEUPDATEINTERVAL"))
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + self.strategyName + "_" + current_time_string(), log_path="./logs")
    self.logger.info(f'{TERM_GREEN}Config loaded ==> user: {self.account_id}, buy_price: {self.buy_price}, sell_price: {self.sell_price}, buy_volume: {self.buy_volume}, sell_volume: {self.sell_volume}, price_update_interval: {self.price_update_interval}{TERM_NFMT}')

    self.orders = []
    self.last_buy_price_updated_ts = 0
    self.last_sell_price_updated_ts = 0

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

      if 'event' in msg and msg['event']=='modifyorder':
        order_modify_succeed = msg['submitted'] if 'submitted' in msg else False
        if not order_modify_succeed:
          self.logger.error(msg)
          data = msg['data']
          if "recvWindow" in msg["message"]:
            self.recv_window +=500
            self.websocket_app.send_command(self.modify_limit_order_msg(self.market, data["orderId"], data["quantity"], data["price"], self.recv_window))
          elif "FAILED balance check" in msg["message"]:
            quantity = Decimal(str(data['quantity'])) - Decimal("0.1")
            self.websocket_app.send_command(self.modify_limit_order_msg(self.market, data["orderId"], quantity, data["price"]))

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
              # 更新价格的时候,需要更新量,不然usd会超过拥有的usd
              quantity = None
              if "remainingQuantity" in order:
                quantity = order["remainingQuantity"]
              elif "remainQuantity" in order:
                quantity = order["remainQuantity"]
              else:
                quantity = order["quantity"]
              new_quantity = str(math.floor(Decimal(str(quantity)) * Decimal(str(order["price"])) / Decimal(self.buy_price) * 10) / 10)
              if (Decimal(new_quantity) > 0):
                self.websocket_app.send_command(self.modify_limit_order_msg(self.market, order["orderId"], new_quantity, self.buy_price))

        # 更新sell_price
        if Decimal(new_sell_price) != Decimal(self.sell_price):
          self.logger.info(f'Update sell_price: {self.buy_price}, {self.sell_price} => {new_sell_price}')
          self.sell_price = new_sell_price
        
          if (cur_ts - self.last_sell_price_updated_ts) > self.price_update_interval:
            self.last_sell_price_updated_ts = int(current_milli_ts())
            for order in self.get_sell_orders():
              quantity = None
              if "remainingQuantity" in order:
                quantity = order["remainingQuantity"]
              elif "remainQuantity" in order:
                quantity = order["remainQuantity"]
              else:
                quantity = order["quantity"]
              # 直接更新sell order的价格
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
      # self.logger.info(msg)
      if 'event' in msg and msg['event']=='orders' and msg['data']:
        self.orders = msg['data']
        self.display_orders()
    except:
      self.logger.error("on_open Error!!!")
      self.logger.error(traceback.format_exc())

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

  def display_orders(self):
    for order in self.orders:
      self.logger.warn(f'Order: {order["orderId"]} - {order["side"]} - {order["price"]} - {order["quantity"]}')
  
  def get_buy_orders(self):
    return list(filter(lambda order: order["side"] == "BUY", self.orders))
  
  def get_sell_orders(self):
    return list(filter(lambda order: order["side"] == "SELL", self.orders))  