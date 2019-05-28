'''
Daxiang trading robot main entry
'''
from src.portfolio import Portfolio
from src.strategy import Strategy
from src.data import Data
from src.web import Web
import src.settings as s
from time import time, sleep


if __name__ == '__main__':
    data = Data()
    strategy = Strategy()
    portfolio = Portfolio(strategy, data)
    web = Web(portfolio)
    try:
        while True:
            sleep(0.5)
    except KeyboardInterrupt:
        data.close()            