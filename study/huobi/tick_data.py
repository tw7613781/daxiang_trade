# -*- coding: utf-8 -*-
# @Time    : 2018/7/13 11:17
# @Author  : xnbo
# @Site    :
# @File    : tick_data.py
# @Software: PyCharm

import time
from common.constant import *
from exchange.tick_data_base import TickDataBase


class TickData(TickDataBase):
    def __init__(self, symbol, exchange, market_broadcast, on_depth_update=None, symbol_type=SPOT):
        super(TickData, self).__init__(symbol, exchange, market_broadcast, on_depth_update, symbol_type)

    def _update_tick_data(self, tick_data):
        if 'tick' in tick_data:
            self.high = tick_data.get('tick', {}).get('high', 0)
            self.last = tick_data.get('tick', {}).get('close', 0)
            self.low = tick_data.get('tick', {}).get('low', 0)
            self.volume = tick_data.get('tick', {}).get('amount', 0)
            self.open = tick_data.get('tick', {}).get('open', 0)
            self.timestamp = tick_data.get('ts', round(time.time() * 1000))

    def _update_depth_data(self, depth_data):
        if 'tick' in depth_data:
            self.local_time = depth_data[LOCAL_TIME]
            self.asks = depth_data.get('tick', {}).get('asks', [])
            self.bids = depth_data.get('tick', {}).get('bids', [])
        self.timestamp = depth_data.get('ts', round(time.time() * 1000))
