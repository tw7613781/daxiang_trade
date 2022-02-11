# -*- coding: utf-8 -*-
# @Time    : 2018/8/2 10:56
# @Author  : xnbo
# @Site    : 
# @File    : market_service.py
# @Software: PyCharm
from os import path
import sys
root_dir = path.dirname(path.dirname(path.dirname(__file__)))
common_dir = path.join(root_dir, "common")
exchange_dir = path.join(root_dir, "exchange")
sys.path.append(root_dir)
sys.path.append(common_dir)
sys.path.append(exchange_dir)

from exchange.service_base import ServiceBase
from common.constant import *
from exchange.websocket_app import MyWebSocketApp
import json
import gzip
import re
import traceback
from os import path
from common.global_utils import *
from exchange.huobi.huobi_utils import HuobiUtils as huobi_utils
from exchange.huobi.tick_data import TickData


class MarketService(ServiceBase):
    
    ID_COUNT = 0
    DEFAULT_MARKET_STEP = '1'
    
    def __init__(self):
        self.con_file = path.join(path.split(path.realpath(__file__))[0], "exchange.json")
        super(MarketService, self).__init__(EXCHANGE_HUOBI, SERVICE_MARKET, self.con_file)
        url = get_json_config(file=self.con_file, section=self.exchange, key="ws_url")
        self.url = url
        self.webscoket_app = MyWebSocketApp(self)
        self.channel_map_symbol = {}

        self.tick_data = {}

        market_step = get_json_config(file=self.con_file, section=self.exchange, key="market_step")
        self.market_step = MarketService.DEFAULT_MARKET_STEP
        if market_step:
            self.market_step = market_step

        self.init_finish_event.set()
        json_msg = {MSG_TYPE: MSG_INIT_EXCHANGE_SERVICE, EXCHANGE: self.exchange,
                    SERVICE_TYPE: self.service_type,
                    TIMESTAMP: round(time.time())}
        self.broadcast(json_msg)
        self.check_market_thread.start()
        
    def on_message(self, msg, ws=None):
        """
		 处理websocket的market数据
		:param msg:
		:return:
		"""
        try:
            # self.logger.info("ON_MESSAGE={}".format(msg))
            msg = gzip.decompress(msg).decode('utf-8')
            msg = json.loads(msg)
            if 'ping' in msg:
                pong = {"pong": msg['ping']}
                self.webscoket_app.send_command(json.dumps(pong))
                return

            channel = msg['ch'] if 'ch' in msg else ''
            if re.search(r'market.(.*).kline', channel, re.I):
                self.tick_data[self.channel_map_symbol[channel]].put_tick_data(msg)
            elif re.search(r'market.(.*).depth', channel, re.I):
                self.tick_data[self.channel_map_symbol[channel]].put_depth_data(msg)
        except:
            self.logger.error("on_message error!  %s " % msg)
            self.logger.error(traceback.format_exc())

    def subscribe(self, msg):
        """
		订阅行情
		:param msg: json格式消息
		:return:
		"""
        try:
            self.logger.info("subscribe method is called, params is: %s" % msg)
            symbol_list = msg.get('symbol_list', [])
            symbol_type_list = msg.get('symbol_type_list', [])
            self.__subscribe_symbol_list(symbol_list, symbol_type_list)
        except:
            self.logger.error("subscribe Error!!!  %s" % msg)
            self.logger.error(traceback.format_exc())

    def __subscribe_symbol_list(self, symbol_list, symbol_type_list):
        """
		 订阅指定symbol的行情
		:param symbol_list:
		:return:
		"""
        for index, symbol in enumerate(symbol_list):
            if symbol not in self.subscribe_symbol_list:
                # 没有订阅过的symbol，需要初始化TickData信息
                # 如果该symbol的tick对象存在，则不再创建，避免反复重连时的内存泄漏风险
                symbol_type = symbol_type_list[index]
                if symbol not in self.tick_data:
                    # 如果需要存储动态盈亏数据，则注册on_depth_update
                    self.tick_data[symbol] = TickData(symbol, self.exchange, market_broadcast=self.broadcast, on_depth_update=self.on_depth_update, symbol_type=symbol_type)
                self.logger.info("subscribe market data for symbol [%s]." % symbol)
                self.subscribe_symbol_list.append(symbol)
                self.subscribe_symbol_type_list.append(symbol_type)

                # 订阅 KLine 数据
                MarketService.ID_COUNT += 1
                msg = {"sub": "market." + symbol + ".kline.1min",
                       "id": huobi_utils.generate_sub_id(SERVICE_MARKET, MarketService.ID_COUNT)}
                self.webscoket_app.send_command(json.dumps(msg))
                self.channel_map_symbol[msg['sub']] = symbol
                # 订阅 Market Depth 数据
                # 目前不支持自定义行情深度，但合并深度行情分step0到step5六种，step0返回150档行情，其他返回20档
                # 通过对比，step5相对step0有明显的精度损失，step1相对没有step0明显差别，故通过step1订阅深度行情
                MarketService.ID_COUNT += 1
                msg = {"sub": "market." + symbol + ".depth.step" + self.market_step,
                       "id": huobi_utils.generate_sub_id(SERVICE_MARKET, MarketService.ID_COUNT)}
                self.webscoket_app.send_command(json.dumps(msg))
                self.channel_map_symbol[msg['sub']] = symbol
                
        self.logger.info("finished subscribe data, subscribeList is %s." % self.subscribe_symbol_list)
        return ','.join(self.subscribe_symbol_list)

if __name__ == '__main__':
        service = MarketService()
        service.exchange_msg_handle_thread.join()
