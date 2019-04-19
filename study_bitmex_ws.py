from bitmex_ws import BitMEXWebsocket
'''
study the data format received from bitmex, method to run the code

open terminal
cd to_dir_contain_the_file
python3
from study_bitmex_ws import trade_data
trade_data()
'''

def trade_data():
    '''
    "trade" subscription data format => real time trade info（成交）, including Buy and Sell info
    [{'timestamp': '2019-04-19T08:03:27.802Z', 'symbol': 'XBTUSD', 'side': 'Sell', 'size': 100, 'price': 5243, 'tickDirection': 'ZeroMinusTick', 'trdMatchID': 'f362e74c-886c-5ebe-ad35-ef1fdf316af4', 'grossValue': 1907300, 'homeNotional': 0.019073, 'foreignNotional': 100}]
    "tradeBin1m": => candle data for 1 minutes
    [{"timestamp": "2019-04-19T08:10:00.000Z", "symbol": "XBTUSD", "open": 5239.5, "high": 5239.5, "low": 5238.5, "close": 5238.5, "trades": 165, "volume": 488144, "vwap": 5239.4425, "lastSize": 3, "turnover": 9317171239, "homeNotional": 93.17171238999997, "foreignNotional": 488144}]
    "tradeBin5m": => candle data for 5 minutes
    "tradeBin1h": => candle data for 1 hour
    "tradeBin1d": => candle data for 1 day
    '''
    endpoint = 'https://www.bitmex.com/api/v1'
    symbol = 'XBTUSD'
    sub_topic = 'tradeBin5m'
    API_KEY = '7LpiutnmX__Zl_YrkPc8c25l'
    API_SECRET = '1u99uZaAwXsmjdOuyJQLHQlxiZW_rPjWqKsaSjFodtTykuP7'

    ws = BitMEXWebsocket(endpoint=endpoint, symbol=symbol, sub_topic=sub_topic, api_key=API_KEY, api_secret=API_SECRET)


def quote_data():
    '''
    "quote" subscription data format => real time quote info (报价), including Buy and Sell info
    [{"timestamp": "2019-04-19T08:20:53.129Z", "symbol": "XBTUSD", "bidSize": 106061, "bidPrice": 5234, "askPrice": 5234.5, "askSize": 945501}, {"timestamp": "2019-04-19T08:20:53.412Z", "symbol": "XBTUSD", "bidSize": 106061, "bidPrice": 5234, "askPrice": 5234.5, "askSize": 955501}, {"timestamp": "2019-04-19T08:20:53.706Z", "symbol": "XBTUSD", "bidSize": 106061, "bidPrice": 5234, "askPrice": 5234.5, "askSize": 1650443}, {"timestamp": "2019-04-19T08:20:53.721Z", "symbol": "XBTUSD", "bidSize": 106061, "bidPrice": 5234, "askPrice": 5234.5, "askSize": 1655443}, {"timestamp": "2019-04-19T08:20:53.908Z", "symbol": "XBTUSD", "bidSize": 106061, "bidPrice": 5234, "askPrice": 5234.5, "askSize": 1670443}]"tradeBin1m": => candle data for 1 minutes
    "quoteBin1m": => candle data for 1 minutes, feels like the average bid and ask info over the minutes
    [{"timestamp": "2019-04-19T08:26:00.000Z", "symbol": "XBTUSD", "bidSize": 1487579, "bidPrice": 5231, "askPrice": 5231.5, "askSize": 452199}]}
    "quoteBin5m": => candle data for 1 hour
    "quoteBin1h": => candle data for 1 hour
    "quoteBin1d": => candle data for 1 day
    '''
    endpoint = 'https://www.bitmex.com/api/v1'
    symbol = 'XBTUSD'
    sub_topic = 'quoteBin1m'
    API_KEY = '7LpiutnmX__Zl_YrkPc8c25l'
    API_SECRET = '1u99uZaAwXsmjdOuyJQLHQlxiZW_rPjWqKsaSjFodtTykuP7'

    ws = BitMEXWebsocket(endpoint=endpoint, symbol=symbol, sub_topic=sub_topic, api_key=API_KEY, api_secret=API_SECRET)


