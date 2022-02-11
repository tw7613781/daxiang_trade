# -*- coding: utf-8 -*-
# @Time    : 2018/8/2 10:52
# @Author  : xnbo
# @Site    : 
# @File    : trade_service.py
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
from exchange.websocket_app import MyWebSocketApp
from common.constant import *
import json
import gzip
import re
import traceback
import common.global_utils as global_utils
from exchange.huobi.huobi_utils import HuobiUtils as huobi_utils
import copy
import time
from exchange.huobi.huobi_api import HuobiApi
from os import path
from common.global_utils import *


class TradeService(ServiceBase):
    ID_COUNT = 0
    
    def __init__(self):
        self.con_file = path.join(path.split(path.realpath(__file__))[0], "exchange.json")
        super(TradeService, self).__init__(EXCHANGE_HUOBI, SERVICE_TRADE, self.con_file)
        self.channel_map_symbol = {}

        # rest接口初始化
        self.huobi_api = HuobiApi(None, self.trade_url, self.api_key, self.secret_key, logger=self.logger)
        
        # 初始化资金信息
        # if self.huobi_api:
        #     msg = {MSG_TYPE: MSG_QRY_BALANCE, EXCHANGE: EXCHANGE_HUOBI}
        #     self.self_queue.put(msg)
        self.init_finish_event.set()
        json_msg = {MSG_TYPE: MSG_INIT_EXCHANGE_SERVICE, EXCHANGE: self.exchange,
                    SERVICE_TYPE: self.service_type,
                    TIMESTAMP: round(time.time())}
        self.broadcast(json_msg)
        # 通知父类通用的内部查询线程开始查询
        self.qry_balance_event.set()
    
    def on_message(self, msg, ws=None):
        """
         处理websocket的trade数据
        :param msg:
        :return:
        """
        try:
            msg = gzip.decompress(msg).decode('utf-8')
            msg = json.loads(msg)
            if 'ping' in msg:
                pong = {"pong": msg['ping']}
                ws.send(json.dumps(pong))
                return
            
            channel = msg['ch'] if 'ch' in msg else ''
            if re.search(r'market.(.*).trade.detail', channel, re.I):
                # broadcast中，针对symbol，price，direction判断是否需要主动查询order信息
                self.logger.debug('Recieved trade detail data:%s' % msg)
                if 'tick' in msg:
                    data_list = msg['tick']['data'] if 'data' in msg['tick'] else []
                    for json_trade_data in data_list:
                        json_temp_trade_data = {}
                        json_temp_trade_data[SYMBOL] = self.channel_map_symbol[channel]
                        json_temp_trade_data[PRICE] = json_trade_data[PRICE]
                        json_temp_trade_data[DIRECTION] = json_trade_data[DIRECTION]
                        json_temp_trade_data[MSG_TYPE] = MSG_TRADE_STATUS
                        # 丢到交易所数据处理队列中处理，在队列处理之后，调用broadcast广播到上层
                        self.exchange_queue.put(json_temp_trade_data)
        except:
            self.logger.error("on_message error!  %s " % msg)
            self.logger.error(traceback.format_exc())

    def subscribe(self, json_msg):
        """
        订阅交易数据
        :param json_msg: json格式消息
        :return:
        """
        try:
            # 暂时屏蔽huobi订阅接口
            pass
            # self.logger.info("subscribe method is called, params is: %s" % json_msg)
            # symbol_list = json_msg.get(SYMBOL_LIST, [])
            # symbol_type_list = json_msg.get(SYMBOL_TYPE_LIST, [])
            # self.__subscribe_symbol_list(symbol_list, symbol_type_list)
        except:
            self.logger.error("subscribe Error!!!  %s" % json_msg)
            self.logger.error(traceback.format_exc())
    
    def __subscribe_symbol_list(self, symbol_list, symbol_type_list):
        """
         订阅指定symbol的交易数据
        :param symbol_list:
        :return:
        """
        for index, symbol in enumerate(symbol_list):
            if symbol not in self.subscribe_symbol_list:
                self.logger.info("subscribe trade data for symbol [%s]." % symbol)
                self.subscribe_symbol_list.append(symbol)
                
                if symbol not in self.subscribe_symbol_type_list:
                    self.subscribe_symbol_type_list.append(symbol_type_list[index])
                # 订阅 Trade Detail 数据
                TradeService.ID_COUNT += 1
                msg = {"sub": "market." + symbol + ".trade.detail",
                       "id": huobi_utils.generate_sub_id(SERVICE_TRADE, TradeService.ID_COUNT)}
                # self.webscoket_app.send_command(json.dumps(msg))
                self.channel_map_symbol[msg['sub']] = symbol
        self.logger.info("finished subscribe data, subscribeList is %s." % self.subscribe_symbol_list)
        return ','.join(self.subscribe_symbol_list)

    def handle_exchange_trade_data(self, json_msg):
        """
        处理交易所推送的trade数据
        :param json_msg:
        :return:
        """
        if json_msg:
            # self.logger.info("ON_EXCHANGE_MSG={}".format(json_msg))
            for (order_id, json_order) in self.order_dict.items():
                # json_msg中的price是字符串
                # 由于trade信息中，price的精度表示与下单时price不一致，所以先转换成float再对比
                # 比如：'0.32300000000'和'0.323'，通过字符串对比返回False，转换成float再对比返回True
                if json_order[SYMBOL] == json_msg[SYMBOL] and json_order[DIRECTION] == json_msg[
                    DIRECTION] and float(json_order[PRICE]) == float(json_msg[PRICE]):
                    # 以下单记录列表中的order作为查询的消息主体，能保留下单请求的相关信息，同时增加订单查询的结果信息
                    self.logger.info("__on_trade method will resolve data: " + json.dumps(json_msg))
                    json_order[ORDER_ID] = order_id
                    self.broadcast(copy.deepcopy(json_order))
                    # global_utils.call_timer(self.broadcast, [copy.deepcopy(json_order)])
                    break
    
    def place_order(self, json_msg):
        try:
            symbol = json_msg.get(SYMBOL, '')
            price = json_msg.get(PRICE, '')
            volume = json_msg.get(VOLUME, '')
            price_type = json_msg.get(PRICE_TYPE, MARKET_PRICE)
            direction = json_msg.get(DIRECTION, '')
            trade_type = '{}-{}'.format(direction, price_type)

            # 下单时间  微秒级时间戳
            json_msg[PLACE_TIME] = round(time.time() * 1000 * 1000)
            # account_id在调用服务时传入（ServiceBase的__args_setup函数）
            rsp = self.huobi_api.send_order(volume, 'api', symbol, trade_type, price)
            # 下单返回时间  微秒级时间戳
            json_msg[PLACE_RSP_TIME] = round(time.time() * 1000 * 1000)
            self.logger.info("place_order rsp is: %s" % rsp)
            # 为None或空，都不处理
            if not rsp:
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                self.broadcast(json_msg)
                return None
            # API返回的status为"ok"，统一转换为"true"
            if STATUS in rsp and huobi_utils.API_RSP_STATUS_OK == rsp[STATUS]:
                json_msg[STATUS] = COMMON_RSP_STATUS_TRUE
                json_msg[STATE] = ORDER_STATE_SUBMITTED
                order_id = rsp.get('data', None)
                json_msg[ORDER_ID] = order_id
                # 订单记录管理
                # 如果订单号重复，不重复记录
                if order_id and not self.order_dict.__contains__(str(order_id)):
                    self.order_dict[str(order_id)] = copy.deepcopy(json_msg)
                else:
                    self.logger.info("order_id is None or repeated order_id [%s]." % order_id)
            else:
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                # 返回错误码和错误信息
                code, msg = huobi_utils.convert_error_code(rsp)
                json_msg[ERROR_CODE] = code
                json_msg[ERROR_MESSAGE] = msg
                
                # 下单出错，广播下单错误消息
                error_rsp = {MSG_TYPE: MSG_PLACE_ORDER_ERROR, EXCHANGE: EXCHANGE_HUOBI,
                             TIME: round(time.time() * 1000 * 1000),
                             ERROR_CODE:json_msg[ERROR_CODE], ERROR_MESSAGE: json_msg[ERROR_MESSAGE]}
                self.broadcast(error_rsp)
            self.broadcast(json_msg)
            return json_msg
        except:
            # 下单出错，广播下单错误消息
            error_rsp = {MSG_TYPE: MSG_PLACE_ORDER_ERROR, EXCHANGE: EXCHANGE_HUOBI,
                         "time": round(time.time() * 1000 * 1000)}
            self.broadcast(error_rsp)

            json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
            self.broadcast(json_msg)
            self.logger.error("placeOrder Error!!!")
            self.logger.error(traceback.format_exc())
            return json_msg

    def cancel_order(self, json_msg):
        try:
            order_id = json_msg.get(ORDER_ID, '')
            # 如果订单已经不在order_dict中，则已经成交或撤单
            if order_id not in self.order_dict:
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                json_msg[ERROR_CODE] = ERROR_CODE_ORDER_NOT_EXIST
                json_msg[ERROR_MESSAGE] = ERROR_MSG_ORDER_NOT_EXIST
                self.broadcast(json_msg)
                return
            
            rsp = self.huobi_api.cancel_order(order_id)
            self.logger.info("cancel_order rsp is: %s" % rsp)
            # 为None或空，都不处理
            if not rsp:
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                self.broadcast(json_msg)
                return
            if STATUS in rsp and huobi_utils.API_RSP_STATUS_OK == rsp[STATUS]:
                # 请求成功 {STATUS: 'ok', 'data': '5254993691'}
                json_msg[STATUS] = COMMON_RSP_STATUS_TRUE
                json_msg[STATE] = ORDER_STATE_CANCELLING
                json_msg['client_order_id'] = rsp.get('data', "")
                self.order_update(order_id, json_msg)
            else:
                # 请求失败 {STATUS: 'error', 'err-code': 'order-orderstate-error', 'err-msg': 'the order state is error', 'data': None}
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                code, msg = huobi_utils.convert_error_code(rsp)
                json_msg[ERROR_CODE] = code
                json_msg[ERROR_MESSAGE] = msg
            self.broadcast(json_msg)
        except:
            json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
            self.broadcast(json_msg)
            self.logger.error("__cancelOrder Error!!!")
            self.logger.error(traceback.format_exc())

    def qry_balance(self, msg):
        """
        查询资金信息
        :param msg:
        :return:
        """
        try:
            # 系统启动时将初始化资金信息，此后，交易所资金变动信息推送过来时，将更新此资金信息
            # 查询时，优先从本地内存取，如果最后更新时间在五分钟以前，将从交易所查询
            # 此处理避免多策略频繁查询接口，超出交易所查询次数限制
            # 统一修改为time.time()获取时间戳，精确到秒
            msg_type = msg.get(MSG_TYPE,"")
            if not self.account_id:
                self.account_id = msg.get(ACCOUNT_ID, None)
            # msg_type为MSG_BALANCE_STATUS时，表明订单状态更新时进行的查询(注意：内部消息处理线程更改了msg_type字段的值)
            # 需要强制向交易所查询最新数据，作为推送消息返回给调用方
            # 如果self.balances中不包含funds，直接去查API
            if msg_type != MSG_BALANCE_STATUS and self.balances and FUNDS in self.balances and (round(time.time()) - self.qry_balances_time) < UPDATE_BALANCE_INTERVAL_TIME:
                # 只共享funds信息，其他信息原样返回
                msg[FUNDS] = self.balances[FUNDS]
                msg[STATUS] = COMMON_RSP_STATUS_TRUE
                # msg[MSG_TYPE] = MSG_QRY_BALANCE_RSP
                if self.account_id:
                    msg[ACCOUNT_ID] = self.account_id
                    self.broadcast(msg)
            else:
                # 不需要传入self.account_id,此处的account_id与查询资金所需account_id没有任何关系
                rsp = self.huobi_api.get_balance()
                self.logger.info("qry_balance rsp is: %s" % rsp)
                # 为None或空，都不处理
                if not rsp:
                    msg[STATUS] = COMMON_RSP_STATUS_FALSE
                    if self.account_id:
                        msg[ACCOUNT_ID] = self.account_id
                        self.broadcast(msg)
                    return
                # API返回status为"ok"，统一转换为'true'
                if STATUS in rsp and huobi_utils.API_RSP_STATUS_OK == rsp[STATUS]:
                    msg[STATUS] = COMMON_RSP_STATUS_TRUE
                    funds = {}
                    data = rsp.get('data', {})
                    rsp_balance_list = data.get('list', "")
                    if rsp_balance_list is not None:
                        for balance in rsp_balance_list:
                            funds_temp = {}
                            # 如果funds不包含当前currency  key，则将该key添加到funds中，value在后面的逻辑更新
                            if balance['currency'] not in funds:
                                funds[balance['currency']] = {}
        
                            funds_temp = funds[balance['currency']]
                            # 目前huobi只有trade(交易余额)和frozen（冻结余额）两种状态
                            if balance[TYPE] == huobi_utils.HUOBI_BALANCE_TYPE_TRADE:
                                funds_temp[BALANCE_TYPE_FREE] = float(balance.get('balance', 0.00))
                            elif balance[TYPE] == huobi_utils.HUOBI_BALANCE_TYPE_FROZEN:
                                funds_temp[BALANCE_TYPE_FREEZED] = float(balance.get('balance', 0.00))
                            else:
                                funds_temp['other'] = float(balance.get('balance', 0.00))

                    funds_rsp = {}
                    funds_rsp.update(msg)
                    funds_rsp[FUNDS] = funds

                    # 记录资金信息和最后更新时间
                    self.qry_balances_time = round(time.time())
                    self.balances = funds_rsp
                    if self.broadcast and self.account_id:
                        funds_rsp[ACCOUNT_ID] = self.account_id
                        self.broadcast(funds_rsp)
                else:
                    msg[STATUS] = COMMON_RSP_STATUS_FALSE
                    code, mssage = huobi_utils.convert_error_code(rsp)
                    msg[ERROR_CODE] = code
                    msg[ERROR_MESSAGE] = mssage
                    if self.account_id:
                        msg[ACCOUNT_ID] = self.account_id
                        self.broadcast(msg)

        except:
            msg[STATUS] = COMMON_RSP_STATUS_FALSE
            if self.account_id:
                msg[ACCOUNT_ID] = self.account_id
                self.broadcast(msg)
                # self.broadcast(msg)
            self.logger.error("__qry_balance Error!!!")
            self.logger.error(traceback.format_exc())

    def qry_order(self, json_msg):
        """
        目前不主动查询订单信息，通过主动上报获取订单  reviewed by xnb
        :param msg:
        :return:
        """
        try:
            order_id = json_msg.get(ORDER_ID, None)
            if order_id is None or order_id == 'None':
                return
            # 当前订单刚开始加载到order_dict后查询订单trade还没初始化或者初始化还未初始化完成
            if not self.huobi_api:
                return
            rsp = self.huobi_api.order_info(order_id)
            self.logger.info("qry_order rsp is: %s" % rsp)
                
            # 为None或空，都不处理
            if not rsp:
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                self.broadcast(json_msg)
                # self.broadcast(msg)
                return
            if "err-msg" in rsp:
                json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
                code, msg = huobi_utils.convert_error_code(rsp)
                json_msg[ERROR_CODE] = code
                json_msg[ERROR_MESSAGE] = msg
                self.broadcast(json_msg)
                return
            # 订单状态：pre-submitted 准备提交, submitting , submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销
            json_order_data = rsp.get('data', {})
            json_msg[STATE] = huobi_utils.convert_order_state(json_order_data.get(STATE, ""))
            # 返回信息只有成交总金额和成交量，无成交价,无均价，目前用总金额除以成交量，作为成交价和均价
            temp_price = 0.0
            if float(json_order_data['field-amount']) != 0.0:
                temp_price = float(json_order_data['field-cash-amount']) / float(json_order_data['field-amount'])
            json_msg[TRADE_PRICE] = temp_price
            json_msg[TRADE_VOLUME] = float(json_order_data['field-amount'])
            json_msg[AVG_PRICE] = temp_price
            # 订单状态更新后的查询资金和删除放在父类service_base中__self_qry_order_thread处理
            self.order_update(order_id, json_msg)
            self.broadcast(json_msg)
        except:
            json_msg[STATUS] = COMMON_RSP_STATUS_FALSE
            self.broadcast(json_msg)
            self.logger.error("qry_order Error!!!")
            self.logger.error(traceback.format_exc())



if __name__ == '__main__':
    service = TradeService()
    service.exchange_msg_handle_thread.join()
    
