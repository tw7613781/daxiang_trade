'''
Provide different strategys. if want to add a new one, just put here.
'''
import pandas as pd

def _macd(df, n_fast=12, n_slow=26, n_signal=9):
    """Calculate MACD, MACD Signal and MACD difference
    :param df: pandas.DataFrame
    :param n_fast: 
    :param n_slow: 
    :param n_signal:
    :return: pandas.DataFrame
    """
    EMAfast = pd.Series(df['close'].ewm(span=n_fast, min_periods=n_slow).mean())
    EMAslow = pd.Series(df['close'].ewm(span=n_slow, min_periods=n_slow).mean())
    MACD = pd.Series(EMAfast - EMAslow, name='macd')
    MACD_signal = pd.Series(MACD.ewm(span=n_signal, min_periods=n_signal).mean(), name='macd_signal')
    MACD_diff = pd.Series(MACD - MACD_signal, name='macd_diff')
    df = df.join(MACD)
    df = df.join(MACD_signal)
    df = df.join(MACD_diff)
    return df

def _crossover(a, b):
    return a[-2] < b[-2] and a[-1] > b[-1]

def _crossunder(a, b):
    return a[-2] > b[-2] and a[-1] < b[-1]

def MACD(df):
    '''
    strategy function read data from ohlcv array with length 50, gives a long or short or nothing signal
    '''
    df = _macd(df)
    if _crossover(df.macd.values, df.macd_signal.values):
        return 'Buy'
    elif _crossunder(df.macd.values, df.macd_signal.values):
        return 'Sell'
    else:
        return 'Nothing'
