'''
it communicates with Bitmex exchange API, fetch all necessary origin info. 
It also becomes the base class for all classes 
'''

import bitmex
import json
import settings as s
import utils as u

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