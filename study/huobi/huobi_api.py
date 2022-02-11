# -*- coding: utf-8 -*-
# @Time    : 2018/8/7 10:56
# @Author  : zxlong
# @Site    :
# @File    : huobi_api.py
# @Software: PyCharm


from exchange.rest_service import RestService
import base64
import datetime
import hashlib
import hmac
import urllib
import urllib.parse
import urllib.request

GET_ACCOUNTS_PATH = "/v1/account/accounts"
GET_BALANCE_PATH = "/v1/account/accounts/{0}/balance"
SEND_ORDER_PATH = "/v1/order/orders/place"
CANCEL_ORDER_PATH = "/v1/order/orders/{0}/submitcancel"
ORDER_INFO_PATH = "/v1/order/orders/{0}"


class HuobiApi(RestService):

    def __init__(self, market_url, trade_url, api_key=None, api_secret=None, logger=None):
        self.logger = logger
        # 行情相关接口的url 暂未使用
        self.market_url = market_url
        # 交易相关接口的url
        self.trade_url = trade_url
        self.api_key = api_key
        self.api_secret = api_secret
        # {'id': 2214685, 'type': 'spot', 'subtype': '', 'state': 'working'}, {'id': 3299764, 'type': 'otc', 'subtype': '', 'state': 'working'}, {'id': 3950464, 'type': 'point', 'subtype': '', 'state': 'working'}
        accounts = self.get_accounts()
        if accounts is not None:
            self.account_id = accounts['data'][0]['id']
        else:
            self.account_id = None

    def get_accounts(self):
        """
        获取account_id
        :return:
        """
        request_path = GET_ACCOUNTS_PATH
        params = {}
        return self.__get(params, request_path)

    def get_balance(self, acct_id=None):
        """
        获取当前账户资产
        :param acct_id
        :return:
        """

        if not acct_id:
            # accounts = self.get_accounts()
            # acct_id = accounts['data'][0]['id'];
            acct_id = self.account_id

        request_path = GET_BALANCE_PATH.format(acct_id)
        params = {"account-id": acct_id}
        return self.__get(params, request_path)

    def send_order(self, amount, source, symbol, _type, price=0):
        """
        创建并执行订单(下单接口)
        :param account_id:
        :param amount:
        :param source: api如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price:
        :return:
        """
        params = {"account-id": self.account_id,
                  "amount": amount,
                  "symbol": symbol,
                  "type": _type,
                  "source": source}
        if price:
            params["price"] = price

        request_path = SEND_ORDER_PATH
        return self.__post(params, request_path)

    def cancel_order(self, order_id):
        """
        撤单操作，针对单个订单
        :param order_id:
        :return:
        """
        params = {}
        request_path = CANCEL_ORDER_PATH.format(order_id)
        return self.__post(params, request_path)

    def order_info(self, order_id):
        """
        查询某个订单
        :param order_id:
        :return:
        """
        params = {}
        request_path = ORDER_INFO_PATH.format(order_id)
        return self.__get(params, request_path)

    def __get(self, params, request_path, need_auth=True):
        """
        需要鉴权的get请求
        :param params:
        :param request_path:
        :param need_auth:
        :return:
        """
        method = 'GET'
        host_url = self.trade_url
        # 需要鉴权的请求
        if need_auth:
            timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            params.update({'AccessKeyId': self.api_key,
                           'SignatureMethod': 'HmacSHA256',
                           'SignatureVersion': '2',
                           'Timestamp': timestamp})
            host_name = urllib.parse.urlparse(host_url).hostname
            host_name = host_name.lower()
            params['Signature'] = self.__create_sign(params, method, host_name, request_path)

        # url = host_url + request_path
        return self.handle_request(host_url, request_path, verb=method, query=params, logger=self.logger)

    # return self.http_get_request(url, params)

    def __post(self, params, request_path, need_auth=True):
        """
        需要鉴权的post请求
        :param params:
        :param request_path:
        :param need_auth:
        :return:
        """
        method = 'POST'
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        host_url = self.trade_url
        # 需要鉴权的请求
        if need_auth:
            timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            params_to_sign = {'AccessKeyId': self.api_key,
                              'SignatureMethod': 'HmacSHA256',
                              'SignatureVersion': '2',
                              'Timestamp': timestamp}
            host_name = urllib.parse.urlparse(host_url).hostname
            host_name = host_name.lower()
            params_to_sign['Signature'] = self.__create_sign(params_to_sign, method, host_name, request_path)

            # url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
            # huobi的签名机制，跟签名相关的数据，都需要编码到URI中
            request_path = request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return self.handle_request(host_url, request_path, verb=method, headers=headers, json=params, logger=self.logger)

    # return self.http_post_request(url, params)

    def __create_sign(self, params, method, host_url, request_path):
        """
        签名算法
        :param params:
        :param method:
        :param host_url:
        :param request_path:
        :return:
        """
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        secret_key = self.api_secret.encode(encoding='UTF8')

        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature
