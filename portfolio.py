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
        self.balance = pd.DataFrame(index=[t.utcnow()], data={'balance':self.data.get_wallet_balance()})
    
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
        current_position = self.data.get_current_position()
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
        if self.balance.balance.values[-1] != current_balance:
            self.balance.append(pd.DataFrame(index=[t.utcnow()], data={'balance': current_balance}))
    
    def portfolio_info(self):
        '''
        返回收益和持仓
        return profit and current position
        '''
        if len(self.balance.index) > 1:
            change_rate = self.balance.pct_change()
            return pd.concat([self.balance, change_rate], axis=1, keys=['balance','rate']), self.data.get_current_position()
        else:
            return self.balance, self.data.get_current_position()
