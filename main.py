'''
Daxiang trading robot main entry
'''
from portfolio import Portfolio
from strategy import Strategy
from data_livetrade import Data
from web import Web
from time import time, sleep
import settings as s

if __name__ == '__main__':
    data = Data()
    strategy = Strategy()
    portfolio = Portfolio(strategy, data)
    web = Web(portfolio)
    while True:
        if round(time()) % s.INTERVAL[s.BIN_SIZE] == 1:
            portfolio.portfolio_rsi()
        sleep(0.5)