'''
it communicates with Bitmex exchange thru restfull api and websocket, fetch all necessary origin info. 
'''

import hashlib
import hmac
import json
import time
import traceback
import urllib
import ssl
import sys
import websocket
import threading
import pandas as pd
from datetime import datetime, timezone, timedelta
import bitmex
import src.settings as s
import src.utils as u

logger = u.get_logger(__name__)

def generate_nonce():
    return int(round(time.time() * 1000))

def generate_signature(secret, verb, url, nonce, data):
    """Generate a request signature compatible with BitMEX."""
    # Parse the url so we can remove the base and extract just the path.
    parsedURL = urllib.parse.urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query

    # print "Computing HMAC: %s" % verb + path + str(nonce) + data
    message = (verb + path + str(nonce) + data).encode('utf-8')

    signature = hmac.new(secret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
    return signature

class Data:
    
    is_running = True
    # below values will be updated by bitmex ws
    excess_margin = None
    wallet_balance = None
    market_price = None
    current_qty = None
    avg_engry_price = None
    data = None
    ohlcv_len = None
    bin_size = None

    def __init__(self):
        self.ohlcv_len = 100
        self.bin_size = s.BIN_SIZE
        self.testnet = s.TEST
        if self.testnet:
            domain = 'testnet.bitmex.com'
        else:
            domain = 'www.bitmex.com'
        self.endpoint = 'wss://' + domain + f'/realtime?subscribe=instrument:{s.SYMBOL},' \
                        f'margin,position:{s.SYMBOL},tradeBin1m:{s.SYMBOL}'
        # bitmex restful api client
        self.client = bitmex.bitmex(test=self.testnet, api_key=s.API_KEY, api_secret=s.API_SECRET)
        # bitmex websocket api
        self.__wsconnect()

    def __wsconnect(self):
        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        self.ws = websocket.WebSocketApp(self.endpoint,
                        on_message=self.__on_message,
                        on_error=self.__on_error,
                        on_close=self.__on_close,
                        on_open=self.__on_open,
                        header=self.__get_auth())
        self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        self.wst.daemon = True
        self.wst.start()

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            time.sleep(1)
            conn_timeout -= 1   

    def get_margin(self):
        '''
        account balance summary
        当前的账户余额相关信息
        '''
        return u.retry(lambda: self.client.User.User_getMargin(currency="XBt").result())

    def get_excess_margin(self):
        '''
        get excess margin
        '''
        if self.excess_margin:
            return self.excess_margin
        else:
            return self.get_margin()['excessMargin']
    
    def get_wallet_balance(self):
        '''
        get account balance
        '''
        if self.wallet_balance:
            return self.wallet_balance
        return self.get_margin()['walletBalance']

    def get_position(self):
        '''
        current order position including open and close position, return None if there is no position
        当前的仓位,如果没有的话，返回None
        '''
        ret = u.retry(lambda: self.client.Position.Position_get(filter=json.dumps({"symbol": s.SYMBOL})).result())
        if ret: return ret[0]
        else: return None

    def get_current_qty(self):
        '''
        get currentQty of position, can be positive and nagative
        '''
        if self.current_qty:
            return self.current_qty
        else:
            ret = self.get_position()
            if ret:
                return ret['currentQty']
            else: return 0
    
    def get_avg_entry_price(self):
        '''
        get avgEntryPrice
        '''
        if self.avg_engry_price:
            return self.avg_engry_price
        else:
            ret = self.get_position()
            if ret:
                return ret['avgEntryPrice']
            else: return 0

    def get_market_price(self):
        '''
        current close price for settings symbol
        当前设置的交易对收盘价格
        '''
        if self.market_price:
            return self.market_price
        else:
            return u.retry(lambda: self.client.Instrument.Instrument_get(symbol=s.SYMBOL).result())[0]["lastPrice"]
    
    def set_leverage(self, leverage):
        '''
        set leverage to position
        '''
        return u.retry(lambda: self.client.Position.Position_updateLeverage(symbol=s.SYMBOL, leverage=leverage).result())

    def fetch_ohlcv(self, start_time, end_time):
        '''
        get data for open-high-low-close-volumn array
        获取open-high-low-close-volumn数组数据
        '''
        left_time = start_time
        right_time = end_time
        data = u.to_data_frame([])

        while True:
            source = u.retry(lambda: self.client.Trade.Trade_getBucketed(symbol=s.SYMBOL, binSize="1m",
                                        startTime=left_time, endTime=right_time, count=500, partial=False).result())
            if len(source) == 0:
                break

            source = u.to_data_frame(source)
            data = pd.concat([data, source])

            if right_time > source.iloc[-1].name + timedelta(minutes=1):
                left_time = source.iloc[-1].name + timedelta(minutes=1)
                time.sleep(1)
            else:
                break
        return data

    def portfolio(self, ohlcv):
        '''
        implemented by portfolio class
        '''
        pass
    
    def update_balance(self):
        '''
        implemented by portfolio class
        '''

    def update_ohlcv(self, update):
        # initial data from RESTAPI
        if self.data is None:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=self.ohlcv_len * s.INTERVAL[self.bin_size][0])
            self.data = self.fetch_ohlcv(start_time, end_time)
        # update data from WS
        else:
            self.data = pd.concat([self.data, update])[1:]
            logger.debug(self.data[-1:])
            re_sample_data = u.resample(self.data, self.bin_size)
            if self.data.iloc[-1].name == re_sample_data.iloc[-1].name + timedelta(minutes=s.INTERVAL[self.bin_size][0]):
                logger.debug(re_sample_data[-1:])
                self.portfolio(re_sample_data)
            self.update_balance()

    def order(self, orderQty, stop=0):
        '''
        This is 'Market' order
        'buy' if orderQty is positive
        'sell' if orderQty is nagative
        '''
        clOrdID = 'Daxiang_' + u.random_str()
        side = 'Buy' if orderQty>0 else 'Sell'       
        if stop == 0:
            # market order
            orderType = 'Market'
            u.retry(lambda: self.client.Order.Order_new(symbol=s.SYMBOL, ordType=orderType, clOrdID=clOrdID,
                                                            side=side, orderQty=orderQty).result())
            u.logging_order(id=clOrdID, type=orderType, side=side,
                            qty=orderQty, price=self.get_market_price())
        else:
            # stop order
            orderType = 'Stop'
            u.retry(lambda: self.client.Order.Order_new(symbol=s.SYMBOL, ordType=orderType, clOrdID=clOrdID,
                                                            side=side, orderQty=orderQty, stopPx=stop).result())
            u.logging_order(id=clOrdID, type=orderType, side=side,
                            qty=orderQty, stop=stop)

    def buy(self, orderQty):
        self.order(orderQty)

    def sell(self, orderQty):
        self.order(-orderQty)

    def stop_buy(self, orderQty, stop):
        self.order(orderQty, stop)
    
    def stop_sell(self, orderQty, stop):
        self.order(-orderQty, stop)

    def get_open_orders(self):
        """
        fetch my all open orders
        """
        open_orders = u.retry(lambda: self.client
                            .Order.Order_getOrders(filter=json.dumps({"symbol": s.SYMBOL, "open": True}))
                            .result())
        open_orders = [o for o in open_orders if o["clOrdID"].startswith('Daxiang')]
        if len(open_orders) > 0:
            return open_orders
        else:
            return None
    
    def cancel_all(self):
        """
        cancel all orders, including stop orders
        """
        orders = u.retry(lambda: self.client.Order.Order_cancelAll().result())
        for order in orders:
            logger.info(f"Cancel Order : (orderID, orderType, side, orderQty, limit, stop) = "
                        f"({order['clOrdID']}, {order['ordType']}, {order['side']}, {order['orderQty']}, "
                        f"{order['price']}, {order['stopPx']})")
        logger.info(f"Cancel All Order")    

    def __get_auth(self):
        api_key = s.API_KEY
        api_secret = s.API_SECRET
        nonce = generate_nonce()
        return [
            "api-nonce: " + str(nonce),
            "api-signature: " + generate_signature(api_secret, 'GET', '/realtime', nonce, ''),
            "api-key:" + api_key
        ]

    def __on_error(self, ws, message):
        logger.error(message)
        logger.error(traceback.format_exc())

    def __on_message(self, ws, message):
        try:
            obj = json.loads(message)
            if 'table' in obj:
                if len(obj['data']) <= 0:
                    return
                table = obj['table']
                data = obj['data']

                if table.startswith("trade"):
                    data[0]['timestamp'] = datetime.strptime(data[0]['timestamp'][:-5], '%Y-%m-%dT%H:%M:%S')
                    self.update_ohlcv(u.to_data_frame(data))

                if table.startswith("instrument"):
                    if 'lastPrice' in data[0]:
                        self.market_price = data[0]['lastPrice']

                elif table.startswith("margin"):
                    if 'excessMargin' in data[0]:
                        self.excess_margin = data[0]['excessMargin']
                    if 'walletBalance' in data[0]:
                        self.wallet_balance = data[0]['walletBalance']

                elif table.startswith("position"):
                    if 'currentQty' in data[0]:
                        self.current_qty = data[0]['currentQty']
                    if 'avgEntryPrice' in data[0]:
                        self.avg_engry_price = data[0]['avgEntryPrice']

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def __on_close(self, ws):
        if self.is_running:
            logger.info("Websocket restart")
            self.__wsconnect()

    def __on_open(self, ws):
        logger.info('bitmex websocket opened')

    def close(self):
        logger.info('bitmex websocket closed')
        self.is_running = False
        self.ws.close()