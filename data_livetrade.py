'''
it communicates with Bitmex exchange API, fetch all necessary origin info. 
'''

import bitmex
import json
import time
import pandas as pd
import settings as s
import utils as u

logger = u.get_logger(__name__)

class Data:

    def __init__(self):
        self.client = bitmex.bitmex(test=s.TEST, api_key=s.API_KEY, api_secret=s.API_SECRET)

    def get_margin(self):
        '''
        account balance summary
        当前的账户余额相关信息
        '''
        return u.retry(lambda: self.client.User.User_getMargin(currency="XBt").result())

    def get_position(self):
        """
        current order position including open and close position, return None if there is no position
        当前的仓位,如果没有的话，返回None
        """
        ret = u.retry(lambda: self.client.Position.Position_get(filter=json.dumps({"symbol": s.SYMBOL})).result())
        if ret: return ret[0]
        else: return None
    
    def get_market_price(self):
        '''
        current close price for settings symbol
        当前设置的交易对收盘价格
        '''
        return u.retry(lambda: self.client.Instrument.Instrument_get(symbol=s.SYMBOL).result())[0]["lastPrice"]
    
    def set_leverage(self, leverage):
        '''
        set leverage to position
        '''
        return u.retry(lambda: self.client.Position.Position_updateLeverage(symbol=s.SYMBOL, leverage=leverage).result())


    def fetch_latest_ohlcv(self, bin_size, length):
        '''
        fetch data for open-high-low-close-volumn array
        获取open-high-low-close-volumn数组数据
        bin_size: data interval, available options: [1m,5m,1h,1d].
        length: length must less than 750, which is the maximum size per reqeust made by Bitmex. 
        It's enough for most strategy, if need more data we can consider using start_time and end_time
        Found that by using start and count pair looping to fetch data is not stable
        '''
        source = u.retry(lambda: self.client.Trade.Trade_getBucketed(symbol=s.SYMBOL, binSize=bin_size,
                                        count=length, reverse=True).result())
        source = u.to_data_frame(source, reverse=True)
        return source

    def order(self, orderQty, stop=0):
        '''
        This is 'Market' order
        'buy' if orderQty is positive
        'sell' if orderQty is nagative
        '''
        clOrdID = 'Daxiang_' + u.random_str()
        side = 'Buy' if orderQty>0 else 'Sell'       
        if stop == 0:
            # market order
            orderType = 'Market'
            u.retry(lambda: self.client.Order.Order_new(symbol=s.SYMBOL, ordType=orderType, clOrdID=clOrdID,
                                                            side=side, orderQty=orderQty).result())
            u.logging_order(logger=logger, id=clOrdID, type=orderType, side=side,
                            qty=orderQty, price=self.get_market_price())
        else:
            # stop order
            orderType = 'Stop'
            u.retry(lambda: self.client.Order.Order_new(symbol=s.SYMBOL, ordType=orderType, clOrdID=clOrdID,
                                                            side=side, orderQty=orderQty, stopPx=stop).result())
            u.logging_order(logger=logger, id=clOrdID, type=orderType, side=side,
                            qty=orderQty, stop=stop)

    def buy(self, orderQty):
        self.order(orderQty)

    def sell(self, orderQty):
        self.order(-orderQty)

    def stop_buy(self, orderQty, stop):
        self.order(orderQty, stop)
    
    def stop_sell(self, orderQty, stop):
        self.order(-orderQty, stop)

    def get_open_orders(self):
        """
        fetch my all open orders
        """
        open_orders = u.retry(lambda: self.client
                            .Order.Order_getOrders(filter=json.dumps({"symbol": s.SYMBOL, "open": True}))
                            .result())
        open_orders = [o for o in open_orders if o["clOrdID"].startswith('Daxiang')]
        if len(open_orders) > 0:
            return open_orders
        else:
            return None
    
    def cancel_all(self):
        """
        cancel all orders, including stop orders
        """
        orders = u.retry(lambda: self.client.Order.Order_cancelAll().result())
        for order in orders:
            logger.info(f"Cancel Order : (orderID, orderType, side, orderQty, limit, stop) = "
                        f"({order['clOrdID']}, {order['ordType']}, {order['side']}, {order['orderQty']}, "
                        f"{order['price']}, {order['stopPx']})")
        logger.info(f"Cancel All Order")