'''
Provide different strategys. if want to add a new one, just put here.
params: pandas dataframe with ohlcv data
return: signal string, 'Buy', or 'Sell', or 'Nothing'
'''
import pandas as pd
import utils as u

class Strategy:

    def __init__(self):
        pass

    def MACD(self, df):
        '''
        strategy function read data from ohlcv array with length 50, gives a long or short or nothing signal
        '''
        df = u.macd(df)
        if u.crossover(df.macd.values, df.macd_signal.values):
            return 'Buy'
        elif u.crossunder(df.macd.values, df.macd_signal.values):
            return 'Sell'
        else:
            return 'Nothing'
