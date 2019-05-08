# coding: UTF-8
import hashlib
import hmac
import json
import time
import traceback
import urllib
import websocket
from datetime import datetime

import settings as s
import utils as u

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


class BitMexWs:
    
    def __init__(self):
        self.testnet = s.TEST
        if self.testnet:
            domain = 'testnet.bitmex.com'
        else:
            domain = 'www.bitmex.com'
        self.endpoint = 'wss://' + domain + f'/realtime?subscribe=instrument:XBTUSD'
        self.ws = websocket.WebSocketApp(self.endpoint,
                             on_message=self.__on_message,
                             on_error=self.__on_error,
                             on_close=self.__on_close,
                             on_open=self.__on_open,
                             header=self.__get_auth())
        self.ws.run_forever()
    
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
        """
        新しいデータを取得した場合
        :param ws:
        :param message:
        :return:
        """
        try:
            # obj = json.loads(message)
            logger.info(message)
            # if 'table' in obj:
            #     if len(obj['data']) <= 0:
            #         return

            #     table = obj['table']
            #     action = obj['action']
            #     data = obj['data']

            #     if table.startswith("tradeBin"):
            #         data[0]['timestamp'] = datetime.strptime(data[0]['timestamp'][:-5], '%Y-%m-%dT%H:%M:%S')
            #         logger.info(table, action, u.to_data_frame([data[0]]))

            #     elif table.startswith("instrument"):
            #         logger.info(table, action, data[0])

            #     elif table.startswith("margin"):
            #         logger.info(table, action, data[0])

            #     elif table.startswith("position"):
            #         logger.info(table, action, data[0])

            #     elif table.startswith("wallet"):
            #         logger.info(table, action, data[0])

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def __on_close(self, ws):
        logger.info('bitmex websocket closed')
        self.ws.close()

    def __on_open(self, ws):
        logger.info('bitmex websocket opened')

if __name__ == '__main__':
    ws = BitMexWs()
