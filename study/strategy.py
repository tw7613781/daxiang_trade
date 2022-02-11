'''
Provide different strategys. if want to add a new one, just put here.
params: pandas dataframe with ohlcv data
return: signal string, 'Buy', or 'Sell', or 'Nothing'
'''
import src.utils as u

logger  = u.get_logger(__name__)

class Strategy:

    def __init__(self):
        pass

    def MACD(self, df):
        '''
        strategy function read data from ohlcv array with length 50, gives a long or short or nothing signal
        '''
        df = u.macd(df)
        logger.debug(f'DIF: {str(df.macd.values[-2])} - {str(df.macd.values[-1])}')
        logger.debug(f'DEA: {str(df.macd_signal.values[-2])} - {str(df.macd_signal.values[-1])}')
        logger.debug(f'BAR: {str(df.macd_diff.values[-2])} - {str(df.macd_diff.values[-1])}')
        if u.crossover(df.macd.values, df.macd_signal.values):
            return 'Buy'
        elif u.crossunder(df.macd.values, df.macd_signal.values):
            return 'Sell'
        else:
            return 'Nothing'

    def RSI(self, df, fast=12, slow=24):
        df = u.rsi(df)
        sma_fast = u.sma(df.close, fast).values[-1]
        sma_slow = u.sma(df.close, slow).values[-1]
        current_rsi = df.rsi.values[-1]
        if current_rsi < 30 and sma_fast > sma_slow:
            return 'Buy'
        elif current_rsi > 70:
            return 'Sell'
        else: return 'Nothing'