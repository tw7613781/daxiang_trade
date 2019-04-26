'''
By utilizing Data class and stratedy methods, the Portfolio will manage risk and be a portal to the system as well
'''

from data_livetrade import Data
from strategy import MACD
from datetime.datetime import utcnow
import settings as s
import pandas as pd
import math

class Portfolio:
    
    def __init__(self):
        self.data = Data()
        self.rate = s.RATE
        self.leverage = s.LEVERAGE
        self.data.set_leverage(self.leverage)
        self.bin = s.BIN_SIZE
        self.balance = pd.DataFrame(index=utcnow(), {'balance':self.data.get_wallet_balance()})
    
    def get_qty(self):
        '''
        calculate order quatity based on initial settings and current position quatity
        '''
        margin = self.data.get_excess_margin()
        price = self.data.get_market_price()
        return math.floor(margin / 100000000 * price * self.leverage * self.rate)

    def run(self):
        qty = self.get_qty()
        ohlcv = self.data.get_latest_ohlcv(self.bin, 50)
        signal = MACD(ohlcv)
        current_position = self.data.get_current_position()
        if signal == 'Buy':
            self.data.buy(qty - current_position)
        elif signal == 'Sell':
            self.data.sell(qty + current_position)
        else: pass
        current_balance = self.data.get_wallet_balance()
        if self.balance.balance.values[-1] != current_balance:
            self.balance.append(pd.DataFrame(index=utcnow(), {'balance': current_balance}))
    
    def portfolio_info(self):
        '''
        返回收益和持仓
        return profit and current position
        '''
        if self.balance.count > 1:
            change_rate = self.balance.pct_change()
            return pd.concat([self.change, change_rate], axis=1, keys=['balance','rate']), self.get_current_position()
        else:
            return self.balance, self.get_current_position
