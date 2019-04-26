'''
Provide different strategys. if want to add a new one, just put here.
'''

import talib

def _macd(close, fastperiod=12, slowperiod=26, signaperiod=9):
    return talib.MACD(close, fastperiod, slowperiod, signaperiod)

def _rsi(close, period=14):
    return talib.RSI(close, period)

def _crossover(a, b):
    return a[-2] < b[-2] and a[-1] > b[-1]

def _crossunder(a, b):
    return a[-2] > b[-2] and a[-1] < b[-1]

def MACD(open=None, close=None, high=None, low=None, volume=None):
    '''
    strategy function read data from ohlcv array, gives a long or short or nothing signal
    '''
    macd, signal, _ = _macd(close)
    if _crossover(macd, signal):
        return 'Buy'
    elif _crossunder(macd, signal):
        return 'Sell'
    else:
        return 'Nothing'
