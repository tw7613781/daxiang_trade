# -*- coding: utf-8 -*-
# @Time    : 2018/7/16 16:21
# @Author  : xnbo
# @Site    : 
# @File    : service_base.py
# @Software: PyCharm

import threading
import traceback
import sys
from os import system, path, getcwd
import time
import json
import queue
import copy
import setproctitle
from getpass import getuser
import random

from common.constant import *
from common.global_utils import *
# from common.zmq_manager import ZmqManager
# from manager.order_manager import OrderManager
# from manager.warning_manager import WarningManager

if is_linux_system():
    import fcntl

class ServiceBase(object):
    def __init__(self, exchange, service_type, config_file=None):
        self.init_finish_event = threading.Event()  # 用来控制服务初始化完成才处理请求
        self.account_id = ""
        self.api_key = None
        self.secret_key = None
        self.passphrase = None
        # self.manager_zmq_sub = None
        # self.manager_zmq_push = None
        # self.service_zmq_pub = None
        # self.service_zmq_pull = None
        self.is_download = False
        # 增加ping_interval的默认值，避免初始化websocket_base时出错
        self.ping_interval = 0
        self.__args_setup(sys.argv)

        self.exchange = exchange
        self.service_type = service_type
        if self.service_type == SERVICE_TRADE:
            title = self.account_id + "_" + self.exchange + "_" + self.service_type
        else:
            title = self.exchange + "_" + self.service_type
        
        if is_windows_system():
            log_path = path.abspath(path.join(getcwd(), "log"))
        else:
            log_path = "/tmp/coin_trade/log/" + getuser() + "/coin_trade_system_v2/"

        self.logger = setup_logger(title, log_path=log_path)
        
        if is_windows_system():
            process_lock_path = path.abspath(path.join(getcwd(), "process_lock"))
        else:
            process_lock_path = "/tmp/coin_trade/process_lock/"
        if not os.path.exists(process_lock_path):
            os.makedirs(process_lock_path)
        process_lock_file = os.path.join(process_lock_path, title + ".lock")

        # 下面代码在linux有效，通过文件锁来实现只有一个进程名字相同的服务运行
        if is_linux_system():
            try:
                self.logger.info("-------- process_lock: " + process_lock_file + " --------")
                fp = open(process_lock_file, 'a+')
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except:
                self.logger.info("-------- " + title + " already exists --------")
                exit()

        setproctitle.setproctitle(title)  # name the process

        if config_file:
            # 现货交易配置
            self.coin_source = get_json_config(file=config_file, section=self.exchange, key="coin_source")
            # 期货交易配置
            self.futures_source = get_json_config(file=config_file, section=self.exchange, key="futures_source")
            # 该变量用于判断行情接收是否异常判定的最大时差，变量单位为秒，该变量需要在实现类通过配置文件重新加载值
            self.tick_max_time_interval = get_json_config(file=config_file, section=self.exchange, key="tick_max_time_interval")
            # 该变量用于判断行情接收是否异常判定的最小时差，变量单位为秒，该变量需要在实现类通过配置文件重新加载值
            self.tick_min_time_interval = get_json_config(file=config_file, section=self.exchange, key="tick_min_time_interval")
            # 初始化行情url
            self.ws_url = get_json_config(file=config_file, section=self.exchange, key="ws_url")
            # 初始化交易url
            self.trade_url = get_json_config(file=config_file, section=self.exchange, key="trade_url")
            # 初始化passphrase
            self.passphrase = get_json_config(file=config_file, section=self.exchange, key="passphrase")
        else:
            self.coin_source = []
            self.futures_source = []
            self.tick_max_time_interval = 5
            self.tick_min_time_interval = 1
            self.ws_url = None
            self.trade_url = None
            self.passphrase = None

        self.subscribe_symbol_list = []
        self.subscribe_symbol_type_list = []
        self.tick_data = {}

        self.order_dict = {}
        self.balances = {}
        # 资金判断锁
        self.balances_lock = threading.Lock()
        self.qry_balances_time = 0
        # 订单状态锁，保证查询订单或者撤单时修改状态时不会冲突
        self.order_lock = threading.Lock()

        self.broadcast_lock = threading.Lock()
        self.manager_msg_lock = threading.Lock()
        self.strategy_qry_balance_lock = threading.Lock()

        # 接收service manager消息队列,存储json数据
        self.manager_queue = queue.Queue()
        # 接收策略消息队列,存储json数据
        self.strategy_queue = queue.Queue()
        # 接收交易所返回消息队列,存储json数据
        self.exchange_queue = queue.Queue()

        self.qry_balance_event = threading.Event()   # 用来标识是否需要查询balance，实现类如果需要初始化查询资金需要在创建好交易所连接后需要self.qry_balance_event.set()

        """init service with zmq"""
        self.zmq_manager = ZmqManager(self.logger)
        self.__init_zmq(self.zmq_manager)

        self.manager_msg_handle_thread = threading.Thread(target=lambda: self.__manager_msg_handle_thread())
        self.manager_msg_handle_thread.daemon = True
        self.manager_msg_handle_thread.start()

        self.strategy_msg_handle_thread = threading.Thread(target=lambda: self.__strategy_msg_handle_thread())
        self.strategy_msg_handle_thread.daemon = True
        self.strategy_msg_handle_thread.start()

        self.exchange_msg_handle_thread = threading.Thread(target=lambda: self.__exchange_msg_handle_thread())
        self.exchange_msg_handle_thread.daemon = True
        self.exchange_msg_handle_thread.start()

        # self.order_manager = None
        # 深度行情更新时，需要回调通知order_manager进行动态盈亏的计算和存储
        # 因此，不管是trade还是market都需要初始化order_manager
        self.order_manager = None  # OrderManager(self.logger)
        # 初始化预警模块，时间检测每一次下单撤单信息
        self.warn_manager = WarningManager(logger=self.logger)
        if self.service_type == SERVICE_TRADE:
            self.self_qry_balance_thread = threading.Thread(target=lambda: self.__self_qry_balance_thread())
            self.self_qry_balance_thread.daemon = True
            self.self_qry_balance_thread.start()

            self.self_qry_handle_thread = threading.Thread(target=lambda: self.__self_qry_order_thread())
            self.self_qry_handle_thread.daemon = True
            self.self_qry_handle_thread.start()

            # self.order_manager = OrderManager(self.logger)
            # 加载当前订单到order_dict中
            self.load_current_order(self.order_manager)

        self.check_market_thread = threading.Thread(target=lambda: self.__check_market_thread())
        self.check_market_thread.daemon = True

        self.logger.info("Initialized %s %s %s ServiceBase.", self.account_id, self.exchange, self.service_type)

    def __args_setup(self, args):
        """
            setup the service properties based on input argument
        Arguments:
            args {list}
            args[0]String : file name
            args[1]String : the service properties dict, contain: account_id, api_key, api_secret, manager_zmq_sub, manager_zmq_push, service_zmq_pub, service_zmq_pull, is_download
            args[1] = "{'account_id': account_id, 'api_key': api_key, 'api_secret': api_secret, 'manager_zmq_sub': manager_zmq_sub, 'manager_zmq_push': manager_zmq_push, 'service_zmq_pub': service_zmq_pub, 'service_zmq_pull': service_zmq_pull, 'is_download': is_download}"
        """
        try:
            if len(args) >= 2:
                properties_dict = json.loads(args[1])
                self.__dict__.update(properties_dict)
        except:
            print(traceback.print_exc())

    def __init_zmq(self, manager):
        self.logger.info("------ Init %s %s ZMQ ------", self.exchange, self.service_type)
        try:
            """add sockets to manager"""
            if self.manager_zmq_push:
                manager.create_socket(name="manager_zmq_push", mode="PUSH", is_bind=False, address=self.manager_zmq_push)
            else:
                self.logger.error("ERROR: manager_zmq_push ports invalid")
            if self.manager_zmq_sub:
                manager.create_socket(name="manager_zmq_sub", mode="SUB", is_bind=False, address=self.manager_zmq_sub, callback=self.receive_manager_msg)
            else:
                self.logger.error("ERROR: manager_zmq_sub ports invalid")
            if self.service_zmq_pub:
                manager.create_socket(name="service_zmq_pub", mode="PUB", is_bind=True, address=self.service_zmq_pub)
            else:
                self.logger.error("ERROR: service_zmq_pub ports invalid")
            if self.service_zmq_pull:
                manager.create_socket(name="service_zmq_pull", mode="PULL", is_bind=True, address=self.service_zmq_pull, callback=self.receive_strategy_msg)
            else:
                self.logger.error("ERROR: service_zmq_pull ports invalid")
        except:
            self.logger.error("__init_zmq is error")
            self.logger.error(traceback.format_exc())

    def receive_manager_msg(self, msg):
        try:
            if self.init_finish_event.wait():
                json_msg = json.loads(msg)
                self.manager_queue.put(json_msg)
        except:
            self.logger.error("receive_manager_msg Error!!!")
            self.logger.error(traceback.format_exc())

    def receive_strategy_msg(self, msg):
        try:
            if self.init_finish_event.wait():
                self.logger.info("ON STRATEGY={}".format(msg))

                json_msg = json.loads(msg)
                self.strategy_queue.put(json_msg)
        except:
            self.logger.error("receive_strategy_msg Error!!!")
            self.logger.error(traceback.format_exc())

    def __manager_msg_handle_thread(self):
        while True:
            try:
                json_msg = self.manager_queue.get()
                msg_type = json_msg.get(MSG_TYPE, '')
                timer = None
                if timer:
                    timer.start()
            except:
                self.logger.error("__strategy_msg_handle_thread Error!!!")
                self.logger.error(traceback.format_exc())

    def __strategy_msg_handle_thread(self):
        while True:
            try:
                json_msg = self.strategy_queue.get()
                msg_type = json_msg.get(MSG_TYPE, '')
                timer = None
                if MSG_PLACE_ORDER == msg_type:
                    json_msg[MSG_TYPE] = MSG_PLACE_ORDER_RSP
                    model_test = json_msg.get(MODEL, MODEL_REAL)
                    if MODEL_TEST == model_test:
                        timer = threading.Timer(TIMER_INTERVAL_NOW, self.place_order_test, [copy.deepcopy(json_msg)])
                    else:
                        timer = threading.Timer(TIMER_INTERVAL_NOW, self.place_order_public, [copy.deepcopy(json_msg)])
                elif MSG_CANCEL_ORDER == msg_type:
                    json_msg[MSG_TYPE] = MSG_CANCEL_ORDER_RSP
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.cancel_order, [copy.deepcopy(json_msg)])
                elif MSG_QRY_BALANCE == msg_type:
                    json_msg[MSG_TYPE] = MSG_QRY_BALANCE_RSP
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.qry_balance_with_lock, [copy.deepcopy(json_msg)])
                elif MSG_QRY_ORDER == msg_type:
                    json_msg[MSG_TYPE] = MSG_QRY_ORDER_RSP
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.qry_order, [copy.deepcopy(json_msg)])
                elif MSG_UPDATE_LEVERAGE == msg_type:
                    json_msg[MSG_TYPE] = MSG_UPDATE_LEVERAGE_RSP
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.update_levelage, [copy.deepcopy(json_msg)])
                elif MSG_SUBSCRIBE == msg_type:
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.subscribe, [copy.deepcopy(json_msg)])
                elif MSG_CURRENT_ORDER == msg_type:
                    json_msg[MSG_TYPE] = MSG_CURRENT_ORDER_RSP
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.qry_current_order, [copy.deepcopy(json_msg)])
                else:
                    self.logger.info('Unknown msg: ' + json.dumps(json_msg))

                if timer:
                    timer.start()
            except:
                self.logger.error("__strategy_msg_handle_thread Error!!!")
                self.logger.error(traceback.format_exc())

    def __exchange_msg_handle_thread(self):
        while True:
            try:
                json_msg = self.exchange_queue.get()
                msg_type = json_msg.get(MSG_TYPE, '')
                timer = None
                if MSG_TRADE_STATUS == msg_type:
                    json_msg[MSG_TYPE] = MSG_ORDER_STATUS
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.handle_exchange_trade_data, [copy.deepcopy(json_msg)])
                elif MSG_ORDER_STATUS == msg_type:
                    json_msg[MSG_TYPE] = MSG_ORDER_STATUS
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.handle_exchange_order_data, [copy.deepcopy(json_msg)])
                elif MSG_BALANCE_STATUS == msg_type:
                    json_msg[MSG_TYPE] = MSG_BALANCE_STATUS
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.handle_exchange_balance_data, [copy.deepcopy(json_msg)])
                elif MSG_POSITION_STATUS == msg_type:
                    json_msg[MSG_TYPE] = MSG_POSITION_STATUS
                    timer = threading.Timer(TIMER_INTERVAL_NOW, self.handle_exchange_position_data, [copy.deepcopy(json_msg)])
                else:
                    self.logger.info('Unknown msg: ' + json.dumps(json_msg))

                if timer:
                    timer.start()
            except:
                self.logger.error("__exchange_msg_handle_thread Error!!!")
                self.logger.error(traceback.format_exc())

    def __self_qry_balance_thread(self):
        while True:
            try:
                if self.qry_balance_event.wait():
                    json_msg = {MSG_TYPE: MSG_BALANCE_STATUS, EXCHANGE: self.exchange}
                    self.qry_balance(json_msg)
                    if self.order_manager:
                        self.order_manager.put_balance_data(self.balances)
                    self.qry_balance_event.clear()

            except:
                self.logger.error("__self_msg_handle_thread Error!!!")
                self.logger.error(traceback.format_exc())

    def __self_qry_order_thread(self):
        day = time.strftime("%Y%m%d")
        qry_order = {}
        while True:
            try:
                # 标记order_dict中是否存在需要查询资金的订单
                is_qry_balance = False
                # 由于遍历字典的时候不能改变字典大小，取出字典的键（order_id）进行遍历
                order_id_list = list(self.order_dict.keys())
                for order_id in order_id_list:
                    current_time = round(time.time() * 1000000)
                    order = self.order_dict.get(order_id, {})
                    if order_id not in qry_order:
                        qry_order[order_id] = {}
                        qry_order[order_id]["qry_count"] = 0    # 记录订单查询次数
                    qry_count = qry_order.get(order_id, {}).get("qry_count", 0)    # 获取订单查询次数
                    qry_order_time = qry_order.get(order_id, {}).get(QRY_ORDER_TIME, None)
                    if qry_order_time is None:
                        qry_order_time = order.get(PLACE_RSP_TIME, current_time)
                    qry_order_time_interval = 200000  # 默认下单后需要等待至少200毫秒再查询订单
                    if 20 < qry_count:
                        qry_order_time_interval = 60000000   # 如果订单查询超过20次，则把订单的查询间隔调整到60秒
                    if (current_time - qry_order_time) > qry_order_time_interval:
                        old_state = order.get(STATE, "")          # 查询订单前存储订单当前状态值
                        order[MSG_TYPE] = MSG_ORDER_STATUS
                        self.qry_order(order)
                        qry_order[order_id][QRY_ORDER_TIME] = current_time    # 存储当前查询订单的时间
                        qry_order[order_id]["qry_count"] = qry_count + 1      # 存储订单查询次数
                        # 临时变量，同一个订单不会保存两次
                        is_save = False
                        # 查询订单后获取订单状态，全部成交或者全部撤销则在order_dict中删除订单。部分成交撤销则去查询资金信息
                        state = self.order_dict.get(order_id, {}).get(STATE, "")  # 查询订单后获取订单当前新的状态值
                        if old_state != state and self.order_manager:       # 如过新旧状态值不相等，则说明状态发生了改变，需要存储到数据库
                            is_save = True
                            self.logger.info("old state change and now put to queue:{}/{}".format(order_id, self.order_dict.get(order_id, {})))
                            self.order_manager.put_order_data(self.order_dict.get(order_id, {}))
                        if state == ORDER_STATE_FILLED or state == ORDER_STATE_CANCELED or state == ORDER_STATE_PARTIAL_CANCELED \
                                or state == ORDER_STATE_REJECTED or state == ORDER_STATE_EXPIRED:
                            with self.order_lock:
                                # 当订单撤销后需要把之前由于下单判断的资金进行解冻
                                if state == ORDER_STATE_CANCELED or state == ORDER_STATE_PARTIAL_CANCELED:
                                    self.is_enough_funds(self.order_dict.get(order_id, {}), True)
                                if self.order_manager and not is_save:       # 删除订单前, 发送订单到order_manager进行存储
                                    self.logger.info("old state change and now put to queue:{}/{}".format(order_id, self.order_dict.get(order_id, {})))
                                    self.order_manager.put_order_data(self.order_dict.get(order_id, {}))
                                self.order_dict.pop(order_id)
                            qry_order.pop(order_id)     # 订单删除后同时删除查询订单字典中存储的数据
                            is_qry_balance = True
                new_day = time.strftime("%Y%m%d")
                if day != new_day:
                    day = new_day
                    is_qry_balance = True    # 日期更新后需要重新查询一次资金imp
                if is_qry_balance:
                    self.qry_balance_event.set()
                time.sleep(0.1)
            except:
                self.logger.error("__self_msg_handle_thread Error!!!")
                self.logger.error(traceback.format_exc())

    def __check_market_thread(self):
        market_status = True   # 行情状态默认值为True
        pre_market_status = True   # 前一个行情状态默认值为True
        while True:
            try:
                """ 
                通过获取订阅的行情数来动态的调整检测行情异常的时差值，如果只有一个symbol的行情，则使用最大时差tick_max_time_interval来作为判定行情异常的时差，
                如果订阅的symbol数大于1，则用最大时差来减去（订阅数-1）得到一个动态的时差值，如果动态时差值小于最小时差tick_min_time_interval，则时差值取最小时差tick_min_time_interval
                时差以秒为单位，和行情中的local_time做时差判断
                """
                tick_keys = self.tick_data.keys()
                tick_count = len(tick_keys)
                tick_time_interval = self.tick_max_time_interval - (tick_count - 1)    # 时间以秒为单位
                if self.tick_min_time_interval > tick_time_interval:
                    tick_time_interval = self.tick_min_time_interval
                if tick_count > 0:

                    time_out_count = 0
                    current_time = round(time.time() * 1000000)
                    time_interval = tick_time_interval * 1000000   # 由于local_time精确到微秒，因此需要把时差精确到微秒
                    # 遍历所有的tick数据，判断tick的接收时间和当前时间的差是否小于判定行情异常的时间间隔
                    for key, tick in self.tick_data.items():
                        if (current_time - tick.local_time) < time_interval:     # 行情接收是时间和当前时间小于行情异常判断时差，该条件只要成立一个，则认为行情正常
                            break
                        else:
                            time_out_count += 1    # 行情接收是时间和当前时间大于行情异常判断时差，需要计数超时的行情个数
                    pre_market_status = market_status    # 在给行情状态值进行修改前，需要存储为前一个行情状态
                    if time_out_count == tick_count:     # 如果行情超时计数和行情总个数相等，则证明所有的行情都超时
                        market_status = False
                    else:
                        market_status = True
                    if pre_market_status != market_status:     # 如果当前行情状态和前一个行情状态不相等，则证明状态发生了改变，需要给策略发送新的状态
                        json_msg = {MSG_TYPE: MSG_MARKET_STATUS, EXCHANGE: self.exchange,
                                    SERVICE_TYPE: self.service_type, STATUS: market_status,
                                    TIMESTAMP: round(time.time())}
                        self.broadcast(json_msg)

                time.sleep(tick_time_interval)
            except:
                self.logger.error("__check_market_thread Error!!!")
                self.logger.error(traceback.format_exc())

    def order_update(self, order_id, order):
        with self.order_lock:
            if order_id in self.order_dict:
                state = self.order_dict[order_id].get(STATE, ORDER_STATE_UNKNOWN)
                if state == ORDER_STATE_FILLED or state == ORDER_STATE_CANCELED or state == ORDER_STATE_PARTIAL_CANCELED \
                        or state == ORDER_STATE_REJECTED or state == ORDER_STATE_EXPIRED:
                    return
                if state == ORDER_STATE_CANCELED or state == ORDER_STATE_PARTIAL_CANCELED or state == ORDER_STATE_REJECTED or state == ORDER_STATE_EXPIRED:
                    self.is_enough_funds(self.order_dict[order_id], cancel=True)
                self.order_dict[order_id].update(order)
                self.order_dict[order_id][MSG_TYPE] = MSG_ORDER_STATUS    # 确保order_dict中的MSG_TYPE为MSG_ORDER_STATUS

    def on_error(self, error):
        """ Called on fatal websocket errors. We exit on these. """
        try:
            self.logger.error("%s __on_error : %s", self.exchange, error)

            msg_type = MSG_MARKET_DISCONNECTED if self.service_type == SERVICE_MARKET else MSG_TRADE_DISCONNECTED
            msg = {MSG_TYPE: msg_type, EXCHANGE: self.exchange, SERVICE_TYPE: self.service_type, TIMESTAMP: round(time.time() * 1000 * 1000)}
            self.broadcast(msg)
        except:
            self.logger.error("on_error Error!!!")
            self.logger.error(traceback.format_exc())

    def on_open(self):
        """ Called when the WS opens. """
        try:
            self.logger.info("%s websocket opened.", self.exchange)

            symbol_list = self.subscribe_symbol_list
            self.subscribe_symbol_list = []
            symbol_type_list = self.subscribe_symbol_type_list
            self.subscribe_symbol_type_list = []
            json_msg = {MSG_TYPE: MSG_SUBSCRIBE, "symbol_list": symbol_list, "symbol_type_list": symbol_type_list}
            self.subscribe(json_msg)

            # socket连接成功，且已经完成初始订阅，广播一个消息
            msg_type = MSG_MARKET_CONNECTED if self.service_type == SERVICE_MARKET else MSG_TRADE_CONNECTED
            msg = {MSG_TYPE: msg_type, EXCHANGE: self.exchange, SERVICE_TYPE: self.service_type, TIMESTAMP: round(time.time() * 1000 * 1000)}
            self.broadcast(msg)
        except:
            self.logger.error("on_open Error!!!")
            self.logger.error(traceback.format_exc())

    def on_close(self):
        """ Called on websocket close."""
        try:
            self.logger.info("%s websocket closed.", self.exchange)
            # socket断开连接时，广播一个消息
            msg_type = MSG_MARKET_DISCONNECTED if self.service_type == SERVICE_MARKET else MSG_TRADE_DISCONNECTED
            msg = {MSG_TYPE: msg_type, EXCHANGE: self.exchange, SERVICE_TYPE: self.service_type, TIMESTAMP: round(time.time() * 1000 * 1000)}
            self.broadcast(msg)
        except:
            self.logger.error("on_close Error!!!")
            self.logger.error(traceback.format_exc())

    def broadcast(self, json_msg):
        """
            broadcast market or trade info
        :param msg:
        :return:
        """
        try:
            if json_msg:
                with self.broadcast_lock:
                    msg = json.dumps(json_msg)
                    self.zmq_manager.send("service_zmq_pub", msg)
                    if SERVICE_TRADE == self.service_type:
                        msg_type = json_msg.get(MSG_TYPE, "")
                        if MSG_QRY_BALANCE_RSP != msg_type and MSG_BALANCE_STATUS != msg_type and MSG_POSITION_STATUS != msg_type:
                            self.logger.info("broadcast: " + msg)
                        self.warn_manager.check_order_msg(json_msg)
        except:
            self.logger.error("broadcast Error!!!")
            self.logger.error(traceback.format_exc())

    def push_msg_to_manager(self, json_msg):
        try:
            if json_msg:
                with self.manager_msg_lock:
                    self.zmq_manager.send("manager_zmq_push", json.dumps(json_msg))
        except:
            self.logger.error("push_msg_to_manager Error!!!")
            self.logger.error(traceback.format_exc())
    # 启动service_base后从数据查询当前订单加载到order_dict中
    def load_current_order(self, order_manager):
        try:
            if order_manager:
                order_list = order_manager.get_current_orders(account_id=self.account_id, exchange=self.exchange)
                self.logger.info("the database current order is: %s" % order_list)
                if order_list:
                    for order in order_list:
                        order_id = order.get("order_id", "")
                        order["trade_day"] = order.get("trade_day", datetime.datetime.now()).strftime("%Y-%m-%d")
                        order["create_time"] = order.get("create_time", datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                        order["update_time"] = order.get("update_time", datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                        self.order_dict[order_id] = order
        except:
            self.logger.error("load_current_order Error!!!")
            self.logger.error(traceback.format_exc())
    def qry_current_order(self, json_msg):
        try:
            client_id = json_msg.get(CLIENT_ID, "")
            strategy_name = json_msg.get(STRATEGY_NAME, "")
            account_id = json_msg.get(ACCOUNT_ID, "")
            strategy_type = json_msg.get(STRATEGY_TYPE, "")

            order_dict = {}
            for order_id, order_msg in self.order_dict.items():
                if (client_id == order_msg.get(CLIENT_ID, "") and
                    strategy_name == order_msg.get(STRATEGY_NAME, "") and
                    account_id == order_msg.get(ACCOUNT_ID, "") and
                    strategy_type == order_msg.get(STRATEGY_TYPE, "")):
                    order_dict[order_id] = order_msg
            if order_dict:
                json_msg["data"] = order_dict
                self.broadcast(json_msg)
        except:
            self.logger.error("qry_current_order Error!!!")
            self.logger.error(traceback.format_exc())

    def is_enough_funds(self, order, cancel=False):
        symbol_type = order.get(SYMBOL_TYPE, SPOT)
        is_enough = None
        if symbol_type == SPOT:
            is_enough = self.is_enough_funds_spot(order, cancel)
        elif symbol_type == FUTURES:
            # is_enough = self.is_enough_funds_futures(order, cancel)
            is_enough = True
        return is_enough

    def is_enough_funds_spot(self, order, cancel=False):
        # 如果没有配置币的信息则不做资金判断默认返回True允许进行后续的下单操作
        if not self.coin_source:
            return True
        else:
            price = order.get(PRICE, 0)
            volume = order.get(VOLUME, 0)
            if price and volume:
                target = None
                source = None
                symbol = str(order.get(SYMBOL, "").lower())
                # 转换后symbol可能的格式：btcusdt, btc_usdt, btc-usdt, eoseth(eth为coin_source), eosht(ht为coin_source).
                for coin in self.coin_source:
                    if coin in symbol and symbol.index(coin) > 0:
                        source = coin
                        target = symbol[:symbol.index(coin)].replace("_", "").replace("-", "")
                        break
                funds = self.balances.get(FUNDS, {})
                if target and source:
                    # 如果下单总价小于balance，则资金不足直接返回。否则计算资金并更新self.balances
                    direction = order.get(DIRECTION, "")
                    if direction == BUY:
                        free = funds.get(source, {}).get(FREE, 0)
                        freezed = funds.get(source, {}).get(FREEZED, 0)
                        total_price = (price * volume)
                        if cancel:
                            funds[source] = {FREE: free + total_price, FREEZED: freezed - total_price}
                        else:
                            if free < total_price:
                                return False
                            else:
                                funds[source] = {FREE: free - total_price, FREEZED: freezed + total_price}
                    elif direction == SELL: # direction == sell
                        free = funds.get(target, {}).get(FREE, 0)
                        freezed = funds.get(target, {}).get(FREEZED, 0)
                        if cancel:
                            funds[source] = {FREE: free + volume, FREEZED: freezed - volume}
                        else:
                            if free < volume:
                                return False
                            else:
                                funds[target] = {FREE: free - volume, FREEZED: freezed + volume}
                    if FUNDS in self.balances:
                        self.balances[FUNDS].update(funds)
                        self.broadcast(self.balances)
                    self.logger.info("place_order msg is %s:" % order)
                    self.logger.info("temp logger is %s:" % self.balances)
                    return True
                else:
                    self.logger.info("the symbol is not in coin_source, please check up the symbol or config!!!")
                    # symbol不在coin_source里面，可能是没有配置，则不做资金判断默认返回True允许进行后续的下单操作
                    return True
            else:
                self.logger.info("the price or volume is None")
                # 市价单不做资金判断默认返回True
                return True

    def on_depth_update(self, tick_data):
        """
        当深度行情更新时，通知订单管理模块进行动态盈亏的计算和存储
        :param tick_data:
        :return:
        """
        if self.order_manager:
            self.order_manager.put_tick_data(tick_data)
        
    
    def is_enough_funds_futures(self, order, cancel=False):
        """
            is_enough_funds_futures, rewritten by derived classes
        :param order:
        :return:
        """

    def place_order_public(self, json_msg):
        """
            下单公共函数，由基类先处理通用业务，再由子类处理各交易所下单业务
        :param json_msg:
        :return:
        """
        try:
            volume = json_msg.get(VOLUME, 0)
            if not volume:
                json_msg[STATUS] = False
                json_msg[ERROR_CODE] = ERROR_CODE_VOLUME_IS_ZERO
                json_msg[ERROR_MESSAGE] = ERROR_MSG_VOLUME_IS_ZERO
                self.broadcast(json_msg)
                return
            # 资金是否足够的判断
            with self.balances_lock:
                is_enough = self.is_enough_funds(json_msg)
            self.logger.info("place_order funds is %s:" % is_enough)
            if is_enough:
                order = self.place_order(json_msg)
                if order and self.order_manager:
                    self.order_manager.put_order_data(order)
                # 下单之后查询资金放在父类中执行
                self.qry_balance_event.set()
            else:
                json_msg[STATUS] = False
                json_msg[ERROR_CODE] = ERROR_CODE_BALANCE_NOT_ENOUGH
                json_msg[ERROR_MESSAGE] = ERROR_MSG_BALANCE_NOT_ENOUGH
                self.broadcast(json_msg)
        except:
            self.logger.info("place_order_public is error")
            self.logger.error(traceback.format_exc())

    def place_order_test(self, json_msg):
        """
            Handling model is test order
        :param json_msg:
        :return:
        """
        # 模拟下单返回
        json_msg[STATUS] = True
        # 以当前时间戳作为order_id, 更新order_id的精度, 扩大到微妙+4位随机数
        json_msg[ORDER_ID] = str(round(time.time() * 1000000)) + str(random.randint(1000,9999))
        json_msg[MSG_TYPE] = MSG_PLACE_ORDER_RSP
        self.broadcast(json_msg)
        # 模拟成交后订单状态返回
        # 单笔成交价
        price = json_msg.get(PRICE, 0)
        volume = json_msg.get(VOLUME, 0)
        json_msg[TRADE_PRICE] = float(price)
        # 已完成成交量
        json_msg[TRADE_VOLUME] = float(volume)
        # 均价:
        json_msg[AVG_PRICE] = float(price)
        json_msg[STATE] = ORDER_STATE_FILLED
        json_msg[MSG_TYPE] = MSG_ORDER_STATUS
        self.broadcast(json_msg)
        if self.order_manager:    # 模拟测试订单写入数据库
            self.order_manager.put_order_data(json_msg)
            self.logger.info("test place order. put msg here:{}".format(json_msg[ORDER_ID]))

    def on_message(self, msg, ws=None):
        """
            Handling websocket callback message, rewritten by derived classes
        :param msg:
        :return:
        """

    def subscribe(self, json_msg):
        """
            subscribe market or trade info, rewritten by derived classes
        :param json_msg:
        :return:
        """

    def place_order(self, json_msg):
        """
            place order, rewritten by derived classes
        :param json_msg:
        :return:
        """

    def cancel_order(self, json_msg):
        """
            cancel order, rewritten by derived classes
        :param json_msg:
        :return:
        """

    def qry_balance(self, json_msg):
        """
            qry balance, rewritten by derived classes
        :param json_msg:
        :return:
        """

    def qry_balance_with_lock(self, json_msg):
        """
        对查询资金请求加锁处理。
        多个客户端查询同一交易所资金信息，逐个查询，那么，第一次查询到的结果缓存，可以作为其他查询到结果
        :param json_msg:
        :return:
        """
        with self.strategy_qry_balance_lock:
            self.qry_balance(json_msg)

    def qry_order(self, json_msg):
        """
            qry order, rewritten by derived classes
        :param json_msg:
        :return:
        """
    def update_levelage(self, json_msg):
        """
            update_levelage order, rewritten by derived classes
        :param json_msg:
        :return:
        """

    def error_code_handle(self, json_msg):
        """
            handle error code, rewritten by derived classes
        :param json_msg:
        :return:
        """

    def handle_exchange_trade_data(self, json_msg):
        """
        处理交易所推送的trade数据
        :param json_msg:
        :return:
        """

    def handle_exchange_order_data(self, json_msg):
        """
        处理交易所推送的order数据
        :param json_msg:
        :return:
        """

    def handle_exchange_balance_data(self, json_msg):
        """
        处理交易所推送的balance数据
        :param json_msg:
        :return:
        """

    def handle_exchange_position_data(self, json_msg):
        """
        处理交易所推送的position数据
        :param json_msg:
        :return:
        """