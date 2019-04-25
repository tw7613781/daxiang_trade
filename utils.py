import time
import os
import base64
import logging
import pandas as pd
import settings as s
from bravado.exception import HTTPError

def retry(func, count=5):
    '''
    Bitmex http request wrapper function for robust purpose.
    For 503 case ("The system is currently overloaded. Please try again later."),
        will not increase index, make request until succeed. 
    '''
    err = None
    i = 0
    while i < count:
        try:
            ret, res = func()
            rate_limit = int(res.headers['X-RateLimit-Limit'])
            rate_remain = int(res.headers['X-RateLimit-Remaining'])
            if rate_remain < 10:
                time.sleep(5 * 60 * (1 + rate_limit - rate_remain) / rate_limit)
            return ret
        except HTTPError as error:
            status_code = error.status_code
            err = error
            if status_code == 503:
                time.sleep(0.5)
                continue
            elif status_code >= 500:
                time.sleep(pow(2, i + 1))
                i = i+1
                continue
            elif status_code == 400 or \
                    status_code == 401 or \
                    status_code == 402 or \
                    status_code == 403 or \
                    status_code == 404 or \
                    status_code == 429:
                raise Exception(error)
            else:
                i = i+1
    raise Exception(err)

def to_data_frame(data, reverse):
    '''
    convert ohlcv data list to pandas frame
    reverse the frame if latest come first
    '''
    data_frame = pd.DataFrame(data, columns=["timestamp", "high", "low", "open", "close", "volume"])
    data_frame = data_frame.set_index("timestamp")
    if reverse:
        data_frame = data_frame.iloc[::-1]
    return data_frame

def random_str():
    '''
    generate a random string
    '''
    return base64.b64encode(os.urandom(5)).decode()

def get_logger(name, log_level=s.LOG_LEVEL):
    '''
    customize logger format
    '''
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger

def logging_order(logger, id, type, side, qty, price=None, stop=None):
    logger.info(f"========= New Order ==============")
    logger.info(f"ID     : {id}")
    logger.info(f"Type   : {type}")
    logger.info(f"Side   : {side}")
    logger.info(f"Qty    : {qty}")
    logger.info(f"Price  : {price}")
    logger.info(f"Stop   : {stop}")
    logger.info(f"======================================")
