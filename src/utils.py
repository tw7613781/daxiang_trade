import time
# import os
# import base64
# import logging
# import pandas as pd

TERM_RED   = '\033[1;31m'
TERM_NFMT  = '\033[0;0m'
TERM_BLUE  = '\033[1;34m'
TERM_GREEN = '\033[1;32m'

def print_error(func_name, err):
    '''
    highlight error info
    '''
    print(f'{TERM_RED}{func_name} - {err}{TERM_NFMT}')

def current_milli_ts() -> str:
    return str(int(time.time() * 1000))

# ########################################################################################################################
# # Logging relates
# ########################################################################################################################
# def get_logger(name, log_level=s.LOG_LEVEL):
#     '''
#     customize logger format
#     '''
#     formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
#     file_handler = logging.FileHandler('daxiang_robot.log')
#     file_handler.setFormatter(formatter)
#     console_handler = logging.StreamHandler()
#     console_handler.setFormatter(formatter)
#     logger = logging.getLogger(name)
#     logger.setLevel(log_level)
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
#     return logger

# def read_log(file):
#     '''
#     read a log file line by line, return a html formatted string
#     '''
#     text = ''
#     if not os.path.isfile(file): return text
#     with open(file,'r') as f:
#         lines = f.readlines()
#     for line in lines:
#         text += line
#         text += '<br>'   
#     return text

# def read_recent_log(file, offset):
#     '''
#     read log from botton with offset
#     offset: should be negative, and it refers bytes
#     '''
#     text = ''
#     if not os.path.isfile(file): return text
#     with open(file, 'rb') as f:
#         try:
#             f.seek(offset, os.SEEK_END)
#             lines = f.readlines()
#             lines = lines[::-1]
#             for line in lines:
#                 text += line.decode()
#                 text += '<br>'
#         except OSError:
#             lines = f.readlines()
#             lines = lines[::-1]
#             for line in lines:
#                 text += line.decode()
#                 text += '<br>'           
#     return text

# def href_wrapper(file):
#     '''
#     return a html formatted string for href
#     '''
#     return f'<a href="http://{s.DASHBOARD_HOST}:{s.DASHBOARD_PORT}/log">{file}</a>'

# def logging_order(id, type, side, qty, price=None, stop=None):
#     logger.info(f"========= New Order ==============")
#     logger.info(f"ID     : {id}")
#     logger.info(f"Type   : {type}")
#     logger.info(f"Side   : {side}")
#     logger.info(f"Qty    : {qty}")
#     logger.info(f"Price  : {price}")
#     logger.info(f"Stop   : {stop}")
#     logger.info(f"======================================")

# ########################################################################################################################
# # Network relates
# ########################################################################################################################
# def retry(func, count=5):
#     '''
#     Bitmex http request wrapper function for robust purpose.
#     For 503 case ("The system is currently overloaded. Please try again later."),
#         will not increase index, make request until succeed. 
#     '''
#     err = None
#     i = 0
#     while i < count:
#         try:
#             ret, res = func()
#             rate_limit = int(res.headers['X-RateLimit-Limit'])
#             rate_remain = int(res.headers['X-RateLimit-Remaining'])
#             if rate_remain < 10:
#                 time.sleep(5 * 60 * (1 + rate_limit - rate_remain) / rate_limit)
#             return ret
#         except HTTPError as error:
#             status_code = error.status_code
#             err = error
#             if status_code == 503:
#                 time.sleep(0.5)
#                 continue
#             elif status_code >= 500:
#                 time.sleep(pow(2, i + 1))
#                 i = i+1
#                 continue
#             elif status_code == 400 or \
#                     status_code == 401 or \
#                     status_code == 402 or \
#                     status_code == 403 or \
#                     status_code == 404 or \
#                     status_code == 429:
#                 logger.error(Exception(error))
#                 raise Exception(error)
#             else:
#                 i = i+1
#     logger.error(Exception(err))
#     raise Exception(err)

# ########################################################################################################################
# # List or string process
# ########################################################################################################################
# def to_data_frame(data, reverse = False):
#     '''
#     convert ohlcv data list to pandas frame
#     reverse the frame if latest come first
#     '''
#     data_frame = pd.DataFrame(data, columns=["timestamp", "high", "low", "open", "close", "volume"])
#     data_frame = data_frame.set_index("timestamp")
#     data_frame = data_frame.tz_localize(None).tz_localize('UTC', level=0)
#     if reverse:
#         data_frame = data_frame.iloc[::-1]
#     return data_frame

# def resample(data_frame, bin_size):
#     resample_time = s.INTERVAL[bin_size][1]
#     return data_frame.resample(resample_time, closed='right').agg({
#         "open": "first",
#         "high": "max",
#         "low": "min",
#         "close": "last",
#         "volume": "sum",
#     })

# def random_str():
#     '''
#     generate a random string
#     '''
#     return base64.b64encode(os.urandom(5)).decode()

# def change_rate(a, b):
#     '''
#     calculate change rate from a to b
#     return percentage with 2 digits
#     '''
#     return round(float((b-a)/a * 100), 2)

# ########################################################################################################################
# # Basic technical analysis
# ########################################################################################################################
# def crossover(a, b):
#     return a[-2] < b[-2] and a[-1] > b[-1]

# def crossunder(a, b):
#     return a[-2] > b[-2] and a[-1] < b[-1]

# def ema(series, periods):
#     return series.ewm(span=periods, adjust=False).mean()

# def sma(series, periods):
#     return series.rolling(periods).mean()

# def macd(df, n_fast=12, n_slow=26, n_signal=9):
#     """Calculate MACD, MACD Signal and MACD difference
#     :param df: pandas.DataFrame
#     :param n_fast: 
#     :param n_slow: 
#     :param n_signal:
#     :return: pandas.DataFrame
#     """
#     EMAfast = ema(df.close, n_fast)
#     EMAslow = ema(df.close, n_slow)
#     MACD = pd.Series(EMAfast - EMAslow, name='macd')
#     MACD_signal = pd.Series(ema(MACD, n_signal), name='macd_signal')
#     MACD_diff = pd.Series(MACD - MACD_signal, name='macd_diff')
#     df = df.join(MACD)
#     df = df.join(MACD_signal)
#     df = df.join(MACD_diff)
#     return df   

# def rsi(df, n=14):
#     close = df.close
#     diff = close.diff(1)
#     which_dn = diff < 0
#     up, dn = diff, diff*0
#     up[which_dn], dn[which_dn] = 0, -up[which_dn]
#     emaup = ema(up, n)
#     emadn = ema(dn, n)
#     RSI = pd.Series(100 * emaup / (emaup + emadn), name='rsi')
#     df = df.join(RSI)
#     return df