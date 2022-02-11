# -*- coding: utf-8 -*-
# @Time    : 2018/7/13 11:17
# @Author  : xnbo
# @Site    : 
# @File    : tick_data_base.py
# @Software: PyCharm

import time
import queue
import threading
import copy
import traceback

from common.constant import *


class TickDataBase(object):
    def __init__(self, symbol, exchange, market_broadcast, on_depth_update=None, symbol_type=SPOT):
        self.symbol = symbol
        self.exchange = exchange  # (string)交易平台
        self.symbol_type = symbol_type  # (string)none:不区分类型 spot:币币 futures:期货
        self.open = 0  # (double)开盘价格
        self.high = 0  # (double)最高价格
        self.last = 0  # (double)最新成交价
        self.low = 0  # (double)最低价格
        self.volume = 0  # (double)成交量(最近的24小时)
        self.limit_high = 0  # (double)最高买入限制价格
        self.limit_low = 0  # (double)最低卖出限制价格
        self.asks = []  # [[double,double]]卖方深[价格,量]
        self.bids = []  # [[double,double]]买方深度[价格,量]
        self.unit_amount = 0  # (double)合约价值
        self.hold_amount = 0  # (double)当前持仓量
        self.contract_id = 0  # (long)合约ID
        self.timestamp = 0  # (long)时间戳
        self.local_time = 0  # (long)本地时间戳

        # 存储已回调数据，用来判断行情是否发生变化需要回调
        self.old_last = 0  # (double)最新成交价
        self.old_asks = []  # [[double,double]]卖方深[价格,量]
        self.old_bids = []  # [[double,double]]买方深度[价格,量]

        # 注册on_market回调函数
        self.__market_broadcast = market_broadcast
        
        # 注册深度行情更新回调函数
        if on_depth_update:
            self.__on_depth_update = on_depth_update

        # 每个交易对都对应一个数据队列，存储交易所推送的ticker和深度行情数据
        self.__tick_data_queue = queue.Queue()
        # 每个交易对都对应一个数据队列，存储交易所推送的ticker和深度行情数据
        self.__depth_data_queue = queue.Queue()

        # ticker和深度行情分两个线程处理   reviewed by xnb
        # 初始化tick_data实体类时，开启ticker数据队列处理线程
        self.__tick_data_thread_handle = threading.Thread(target=lambda: self.__tick_data_thread())
        self.__tick_data_thread_handle.daemon = True
        self.__tick_data_thread_handle.start()

        # 初始化tick_data实体类时，开启深度行情数据队列处理线程
        self.__depth_data_thread_handle = threading.Thread(target=lambda: self.__depth_data_thread())
        self.__depth_data_thread_handle.daemon = True
        self.__depth_data_thread_handle.start()

    def get_tick_data(self):
        """
        获取实体类的字典形式数据
        :return:
        """
        # 增加了msg_type，避免在broadcast函数中更新此字段
        dict_data = {MSG_TYPE: MSG_MARKET_DATA, TK_SYMBOL: self.symbol, TK_EXCHANGE: self.exchange, TK_SYMBOL_TYPE: self.symbol_type, TK_OPEN: self.open, TK_HIGH: self.high,
                     TK_LAST: self.last, TK_LOW: self.low, TK_VOLUME: self.volume, TK_LIMIT_HIGH: self.limit_high, TK_LIMIT_LOW: self.limit_low,
                     TK_ASKS: self.asks, TK_BIDS: self.bids, TK_UNIT_AMOUNT: self.unit_amount, TK_HOLD_AMOUNT: self.hold_amount, TK_CONTRACT_ID: self.contract_id,
                     TK_TIMESTAMP: self.timestamp, TK_LOCAL_TIME: self.local_time}
        return dict_data

    def put_tick_data(self, json_msg):
        """
        往数据队列插入ticker数据
        :param json_msg:
        :return:
        """
        if json_msg:
            self.__tick_data_queue.put(json_msg)

    def __tick_data_thread(self):
        """
        ticker数据队列处理线程
        :return:
        """
        while True:
            try:
                json_msg = self.__tick_data_queue.get()
                if json_msg:
                    self._update_tick_data(json_msg)
            except:
                print(traceback.format_exc())

    def put_depth_data(self, json_msg):
        """
        往数据队列插入深度行情数据
        :param json_msg:
        :return:
        """
        if json_msg:
            json_msg[LOCAL_TIME] = round(time.time() * 1000000)
            self.__depth_data_queue.put(json_msg)

    def __depth_data_thread(self):
        """
        深度行情数据队列处理线程
        :return:
        """
        while True:
            try:
                json_msg = self.__depth_data_queue.get()
                if json_msg:
                    self._update_depth_data(json_msg)
                    if self.old_last != self.last or self.old_asks != self.asks or self.old_bids != self.bids:
                        self.old_last = copy.deepcopy(self.last)
                        self.old_asks = copy.deepcopy(self.asks)
                        self.old_bids = copy.deepcopy(self.bids)
                        json_data = self.get_tick_data()
                        self.__market_broadcast(json_data)
                        if self.__on_depth_update:
                            self.__on_depth_update(json_data)
            except:
                print(traceback.format_exc())

    def _update_tick_data(self, tick_data):
        """
            update tick data, rewritten by derived classes
        :param tick_data: tick data dict
        :return:
        """

    def _update_depth_data(self, depth_data):
        """
            update depth data, rewritten by derived classes
        :param depth_data: depth data dict
        :return:
        """

