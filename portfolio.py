'''
By utilizing Data class and stratedy methods, the Portfolio will manage risk and be a portal to the system as well
'''

from data_livetrade import Data
from strategy import MACD
import settings as s
import math

class Portfolio:
    
    def __init__(self):
        self.data = Data()
        # rate = order amount / total balance
        self.rate = s.RATE
        # leverage x
        self.leverage = s.LEVERAGE
        self.data.set_leverage(self.leverage)
        self.bin = s.BIN_SIZE
    
    def get_qty(self):
        '''
        calculate order quatity based on initial settings
        '''
        margin = self.data.get_margin()['excessMargin']
        price = self.data.get_market_price()
        return math.floor(margin / 100000000 * price * self.leverage * self.rate)

    def run(self):
        qty = self.get_qty()
        # ohlcv = self.data.