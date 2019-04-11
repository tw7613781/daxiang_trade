import logging
import os
import sys
import importlib
from decimal import Decimal

import settings

def import_path(fullpath):
    """
    Import a file with full path specification. Allows one to
    import from anywhere, something __import__ does not do.
    """
    path, filename = os.path.split(fullpath)
    filename, ext = os.path.splitext(filename)
    sys.path.insert(0, path)
    module = importlib.import_module(filename, path)
    importlib.reload(module)  # Might be out of date
    del sys.path[0]
    return module

def setup_custom_logger(name, log_level=settings.LOG_LEVEL):
    '''
    customize logger format
    '''
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger

def toNearest(num, tickSize):
    '''
    Given a number, round it to the nearest tick. Very useful for sussing float error
    out of numbers: e.g. toNearest(401.46, 0.01) -> 401.46, whereas processing is
    normally with floats would give you 401.46000000000004.
    Use this after adding/subtracting/multiplying numbers.
    '''
    tickDec = Decimal(str(tickSize))
    return float((Decimal(round(num / tickSize, 0)) * tickDec))