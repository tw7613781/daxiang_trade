'''
By utilizing Data class and stratedy methods, the Portfolio will manage risk and be a portal to the system as well
'''

from data_livetrade import Data
from strategy import MACD
from datetime import datetime as t
import settings as s
import utils as u
import pandas as pd
import math

logger = u.get_logger(__name__)

class Portfolio:
    
    def __init__(self):
        self.data = Data()
        self.rate = s.RATE
        self.leverage = s.LEVERAGE
        self.data.set_leverage(self.leverage)
        self.bin = s.BIN_SIZE
        self.balance = [(t.now(), self.data.get_wallet_balance(), 0)]
    
    def get_qty(self):
        '''
        calculate order quatity based on initial settings and current position quatity
        '''
        margin = self.data.get_excess_margin()
        price = self.data.get_market_price()
        return math.floor(margin / 100000000 * price * self.leverage * self.rate)

    def run(self):
        '''
        main process of portfolio
        '''
        ohlcv = self.data.get_latest_ohlcv(self.bin, 50)
        signal = MACD(ohlcv)
        logger.info(f'signal: {signal}')
        current_position = self.data.get_current_position()[0]
        if signal == 'Buy':
            if current_position != 0:
                self.data.order(-current_position)
            qty = self.get_qty()
            self.data.buy(qty)
        elif signal == 'Sell':
            if current_position != 0:
                self.data.order(-current_position)
            qty = self.get_qty()
            self.data.sell(qty)
        else: pass
        current_balance = self.data.get_wallet_balance()
        previous_balance = self.balance[-1][1]
        if current_balance != previous_balance:
            self.balance.append((t.now(), current_balance, 
            round((current_balance - previous_balance)/previous_balance,4)))
    
    def portfolio_info(self):
        '''
        返回收益和持仓
        return profit and current position
        '''
        return self.balance, self.data.get_current_position()
