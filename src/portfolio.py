'''
By utilizing Data class and stratedy methods, the Portfolio will manage risk and be a portal to the system as well
'''
from datetime import datetime as t
import src.settings as s
import src.utils as u
import math

logger = u.get_logger(__name__)

class Portfolio:
    
    def __init__(self, strategy, data):
        '''
        initial portfolio instance with strategy instance and data instance
        '''
        self.data = data
        self.strategy = strategy
        self.rate = s.RATE
        self.leverage = s.LEVERAGE
        self.bin = s.BIN_SIZE
        self.balance = [(t.now(), self.data.get_wallet_balance(), 0, 0)]
        self.set_leverage(self.leverage)
        self.data.portfolio = self.portfolio_macd
        self.data.update_balance = self.update_balance
    
    def set_leverage(self, leverage):
        self.data.set_leverage(leverage)
    
    def get_qty(self):
        '''
        calculate order quatity based on initial settings and current position quatity
        '''
        margin = self.data.get_excess_margin()
        price = self.data.get_market_price()
        return math.floor(margin / 100000000 * price * self.leverage * self.rate)

    def portfolio_macd(self, ohlcv):
        '''
        main process of portfolio
        '''
        signal = self.strategy.MACD(ohlcv)
        logger.debug(f'signal: {signal}')
        current_position = self.data.get_current_qty()
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
    
    def portfolio_rsi(self, ohlcv):
        '''
        alternative portfolio
        '''
        logger.debug(f'close price is: {ohlcv.close.values[-1]}')
        signal = self.strategy.RSI(ohlcv)
        logger.info(f'signal: {signal}')
        current_position = self.data.get_current_qty()
        if signal == 'Buy':
            if current_position < 0:
                self.data.order(-current_position)
                qty = self.get_qty()
                self.data.buy(qty)
        elif signal == 'Sell':
            if current_position > 0:
                self.data.order(-current_position)
                qty = self.get_qty()
                self.data.sell(qty)
        else: pass    

    def update_balance(self):
        current_balance = self.data.get_wallet_balance()
        previous_balance = self.balance[-1][1]
        if current_balance != previous_balance:
            self.balance.append(
                (t.now(), 
                current_balance,
                u.change_rate(previous_balance, current_balance),
                u.change_rate(self.balance[0][1], current_balance)))
    
    def portfolio_info(self):
        '''
        返回收益和持仓
        return profit and current position
        '''
        return self.balance, self.data.get_current_qty(), self.data.get_avg_entry_price()
