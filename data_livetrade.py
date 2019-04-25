'''
it communicates with Bitmex exchange API, fetch all necessary origin info. 
It also becomes the base class for all classes 
'''

import bitmex
import json
import time
import pandas as pd
import settings as s
import utils as u

logger = u.get_logger(__name__)

class Data:
    position = None
    margin = None
    market_price = None
    def __init__(self):
        self.client = bitmex.bitmex(test=s.TEST, api_key=s.API_KEY, api_secret=s.API_SECRET)

    def get_margin(self):
        '''
        account balance
        当前的账户余额
        '''
        self.margin=u.retry(lambda: self.client
                                        .User.User_getMargin(currency="XBt").result())
        return self.margin

    def get_position(self):
        """
        current order position, return None if there is no ordering
        当前的仓位,如果没有的话，返回None
        """
        ret = u.retry(lambda: self.client
                                  .Position.Position_get(filter=json.dumps({"symbol": s.SYMBOL})).result())
        if len(ret) > 0:
            self.position = ret[0]
        else: self.position = None
        return self.position
    
    def get_market_price(self):
        '''
        current close price for settings symbol
        当前设置的交易对收盘价格
        '''
        self.market_price = u.retry(lambda: self.client
                                                .Instrument.Instrument_get(symbol=s.SYMBOL).result())[0]["lastPrice"]
        return self.market_price

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

    def order(self, price, orderQty):
        '''
        This is 'Limit' order
        'buy' if orderQty is positive
        'sell' if orderQty is nagative
        '''
        if price <= 0 or stopPx <= 0:
            raise Exception('price must >= 0')
        clOrdID = 'Daxiang_' + u.random_str()
        orderType = 'Limit'
        u.retry(lambda: self.client.Order.Order_new(symbol=s.SYMBOL, ordType=orderType, clOrdID=clOrdID,
                                                        orderQty=orderQty, price=price).result())
        u.logging_order(logger=logger, id=clOrdID, type=orderType, side='Buy' if orderQty>0 else 'Sell',
                        qty=orderQty, price=price)

    def buy(self, price, orderQty, stopPx):
        pass 

    def sell(self, price, orderQty, stopPx):
        pass
               
    

        #     time.sleep(0.5)
        # clOrdID = 'Daxiang_' + u.random_str()
        # orderType = 'Stop'
        # u.retry(lambda: self.client.Order.Order_new(symbol=s.SYMBOL, ordType=orderType, clOrdID=clOrdID,
        #                                                 orderQty=orderQty, stopPx=stopPx).result())
        # u.logging_order(logger=logger, id=clOrdID, type=orderType, side='Buy' if orderQty>0 else 'Sell',
        #                 qty=orderQty, stop=stopPx)