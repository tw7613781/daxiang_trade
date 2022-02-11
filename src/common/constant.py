# -*- coding: utf-8 -*-

"""
目录
1. 普通-无前缀
2. 信息-MSG前缀
3. 交易所-EXCHANGE前缀
4. 订单相关
5. tick_data 相关字符串
6. 进程相关
7. zmq端口名称
 . 标点符号
"""

"""
_____________________________________________________
1. 普通字符串定义
"""

# id
ACCOUNT_ID = "account_id" 
CLIENT_ID = "client_id"
GROUP_ID = "group_id"
ORDER_ID = "order_id"
INIT_ORDER_ID = "init_order_id"
CONTRACT_ID = "contract_id"

# 交易方向
DIRECTION = "direction"
BUY = "buy"
SELL = "sell"
ASKS = "asks"                                                           # 卖
BIDS = "bids"                                                           # 买
OPEN_POSITION = "open"                                                  # 开仓动作
CLOSE_POSITION = "close"                                                # 平仓动作

# 价格类型
PRICE = "price"
OPEN_PRICE = "open"
HIGH_PRICE = "high"
LAST_PRICE = "last"
LOW_PRICE = "low"
CLOSE_PRICE = "close"
AVG_PRICE = "avg_price" 
LIMIT_HIGH_PRICE = "limit_high" 
LIMIT_LOW_PRICE = "limit_low" 
LIMIT_PRICE = "limit"
MARKET_PRICE = "market"

# 服务类型
SERVICE_TYPE = "service_type"
SERVICE_MARKET = "market"
SERVICE_TRADE = "trade"

# 订单字段
VOLUME = "volume"
SIG_TRADE_VOLUME = "sig_trade_volume"
TRADE_PRICE = "trade_price"
TRADE_VOLUME = "trade_volume" 
UNIT_AMOUNT = "unit_amount"
HOLD_AMOUNT = "hold_amount"
LIMIT = "limit"
REPEATS = "repeats"
EXCHANGE = "exchange"
CLIENT = "client"
ORDER = "order"


STATE = "state" 
STATUS = "status"
SYMBOL = "symbol"
STRATEGY_NAME = "strategy_name"
STRATEGY_TYPE = "strategy_type"
PRICE_TYPE = "price_type"
PRODUCT_TYPE = "product_type"
SYMBOL_TYPE = "symbol_type"
SPOT = "spot"                                                           # symbol_type的值
FUTURES = "futures"                                                     # symbol_type的值
ARBITRAGE = "arbitrage"
COMB_OFFSET_FLAG = "comb_offset_flag"
MODEL = "model"                                                         # 表示订单测试或者实盘的key
MODEL_TEST = "test"                                                     # 表示订单测试或者实盘的value: 模拟交易模式
MODEL_REAL = "real"                                                     # 表示订单测试或者实盘的value: (默认)实盘交易模式

WATCH = "watch"
MESSAGE = "message"
CODE = "code"
TICKER = "ticker"
DEPTH = "depth"

# time
TIMESTAMP = "timestamp"
LOCAL_TIME = "local_time"
PLACE_TIME = "place_time"
PLACE_RSP_TIME = "place_rsp_time"
TICK_TIME = "tick_time"
STRATEGY_PLACE_TIME = "strategy_place_time"
QRY_ORDER_TIME = "qry_order_time"

# error
ERROR = "error"
ERROR_CODE = "error_code"
ERROR_MESSAGE = "error_message"

# key
API_KEY ="api_key"
SECRET_KEY ="secret_key"

# python
QUEUE_SIZE_UNLIMITED = -1
"""
_____________________________________________________
2. 信息类型 message type  以MSG前缀
"""
MSG_TYPE = "msg_type"
MSG_MARKET_DATA = "market_data"
MSG_MARKET_STATUS = "market_status"
MSG_SUBSCRIBE = "subscribe"
MSG_PLACE_ORDER = "place_order"
MSG_PLACE_ORDER_RSP = "place_order_rsp"
MSG_CANCEL_ORDER = "cancel_order"
MSG_CANCEL_ORDER_RSP = "cancel_order_rsp"
MSG_CURRENT_ORDER = "current_order"
MSG_CURRENT_ORDER_RSP = "current_order_rsp"

# balance
MSG_QRY_BALANCE = "qry_balance"
MSG_QRY_BALANCE_RSP = "qry_balance_rsp"
MSG_BALANCE_STATUS = "balance_status"
MSG_TRADE_STATUS = "trade_status"

# order
MSG_QRY_ORDER = "qry_order"
MSG_QRY_ORDER_RSP = "qry_order_rsp"
MSG_GET_ALL_ORDERS = "qry_all_orders"
MSG_GET_ALL_ORDERS_RSP = "qry_all_orders_rsp"
MSG_ORDER_STATUS = "order_status"

# position
MSG_QRY_POSITION = "qry_position"
MSG_QRY_POSITION_RSP = "qry_position_rsp"
MSG_POSITION_STATUS = "position_status"




MSG_INIT_EXCHANGE_SERVICE = "init_exchange_service"                     # 初始化消息类型
MSG_MARKET_CONNECTED = "market_connected"                               # 行情通道连接成功的消息类型
MSG_MARKET_DISCONNECTED = "market_disconnected"                         # 行情通道断开连接的消息类型
MSG_TRADE_CONNECTED = "trade_connected"                                 # 交易通道连接成功的消息类型
MSG_TRADE_DISCONNECTED = "trade_disconnected"                           # 交易通道断开连接的消息类型
MSG_PLACE_ORDER_ERROR = "place_order_error"                             # 下单失败广播消息的消息类型

MSG_UPDATE_LEVERAGE = "update_leverage"                                 # 更新杠杆
MSG_UPDATE_LEVERAGE_RSP = "update_leverage_rsp"


MSG_LOGIN = "login"                                                     # 用户登录
MSG_LOGIN_RSP = "login_rsp"                                             # 用户登录
MSG_REQUIRE_RUNNING_PROCESS = "require_running_process"                 # 请求正在运行的进程
MSG_REQUIRE_MARKET_SOCKETS = "require_market_sockets"                   #请求正在运行的行情socket
MSG_REQUIRE_TRADE_SOCKETS = "require_trade_sockets"                     #请求正在运行的行情socket

MSG_RUNNING_PROCESS = "running_process"                                 # 信息类型:正在运行的进程.
MSG_MARKET_SOCKETS = "market_sockets"
MSG_TRADE_SOCKETS = "trade_sockets"


"""
_____________________________________________________
3. 交易所   以EXCHANGE前缀
"""
EXCHANGE_OKEX ="okex"
EXCHANGE_HUOBI ="huobi"
EXCHANGE_BITMEX ="bitmex"
EXCHANGE_BINANCE ="binance"
EXCHANGE_HITBTC = "hitbtc"
EXCHANGE_BITFINEX = "bitfinex"
EXCHANGE_FCOIN = "fcoin"
EXCHANGE_GDAX = "coinbase"
EXCHANGE_58COIN = "58coin"
EXCHANGE_BIGONE = "bigone"
EXCHANGE_BI = "bi"
EXCHANGE_BITSTAMP = "bitstamp"
EXCHANGE_COINBASE = "coinbase"


DEFAULT_MARKET_DEPTH = "20"
# binance 订阅1挡行情
DEFAULT_MARKET_DEPTH_ONE = "1"
# tradeserice rsp返回
MSG = "msg"
EXECUTEDQTY = "executedQty"
ORIGQTY = "origQty"
LOCKED = "locked"
ASSET = "asset"

SIDE = "side"
TYPE = "type"
FUNDS = "funds"
BALANCES = "balances"
UPDATE_TIME = "update_time"
FREE = "free"
FREEZED = "freezed"
TIME = "time"
CANCEL = "cancel"
SYMBOL_LIST = "symbol_list"
SYMBOL_TYPE_LIST = "symbol_type_list"
DATA = "data"
TABLE = "table"
ACTION = "action"
FILTER = "filter"
SUCCESS = "success"
INSTRUMENT = "instrument"
ORDERBOOK10 = "orderBook10"
MARGIN = "margin"
INSERT = "insert"
UPDATE = "update"
ORDERS = "orders"
POSITION = "position"
"""
_____________________________________________________
4. 订单相关   
"""
ORDER_STATE_UNKNOWN = -1                                                # 未知
ORDER_STATE_REJECTED = -2                                               # 拒绝
ORDER_STATE_PRE_SUBMITTED = 0                                           # 准备提交
ORDER_STATE_SUBMITTING = 1                                              # 提交中
ORDER_STATE_SUBMITTED = 2                                               # 已提交
ORDER_STATE_PARTIAL_FILLED = 3                                          # 部分成交
ORDER_STATE_FILLED = 4                                                  # 完全成交
ORDER_STATE_CANCELLING = 5                                              # 撤单处理中
ORDER_STATE_PARTIAL_CANCELED = 6                                        # 部分成交撤销
ORDER_STATE_CANCELED = 7                                                # 已撤销
ORDER_STATE_EXPIRED = 8                                                 # 订单过期
ORDER_STATE_SUSPENDED = 9                                               # 暂停

"""balance type after format"""
BALANCE_TYPE_FREEZED = "freezed"
BALANCE_TYPE_FREE = "free"
BALANCE_TYPE_BORROW = "borrow"

"""status of common rsp"""
COMMON_RSP_STATUS_TRUE = True
COMMON_RSP_STATUS_FALSE = False

MARKET_DEPTH = "market_depth"

DEFAULT_DEPTH = 20
"""更新资金信息的间隔时间为5分钟"""
UPDATE_BALANCE_INTERVAL_TIME = 5 * 60

"""json section"""
DATA_PROXY = "data_proxy"

# timer定时器执行间隔，0表示立即执行
TIMER_INTERVAL_NOW = 0


"""
_____________________________________________________
5. tick_data 相关字符串
"""

TK_SYMBOL = "symbol"
TK_EXCHANGE = "exchange"
TK_SYMBOL_TYPE = "symbol_type"
TK_OPEN = "open"
TK_HIGH = "high"
TK_LAST = "last"
TK_LOW = "low"
TK_VOLUME = "volume"
TK_LIMIT_HIGH = "limit_high"
TK_LIMIT_LOW = "limit_low"
TK_ASKS = "asks"
TK_BIDS = "bids"
TK_UNIT_AMOUNT = "unit_amount"
TK_HOLD_AMOUNT = "hold_amount"
TK_CONTRACT_ID = "contract_id"
TK_TIMESTAMP = "timestamp"
TK_LOCAL_TIME = "local_time"



"""
_____________________________________________________
6. 进程相关
"""
PROCESS = "process"
PROC_DEAD = 0
PROC_ALIVE = 1
SERVICE_MANAGER = "service_manager"
ORDER_MANAGER = "order_manager"
MARKET_SERVICE = "market_service"
TRADE_SERVICE = "trade_service"
IP = "ip"
CIPHER = "cipher"
PROTOCOL = "protocol"
ADDRESS = "address"
NAME = "name"
LOCAL_ADDRESS = "local_address"
PUBLIC_ADDRESS = "public_address"
PARAMETER = "parameter"


"""
_____________________________________________________
7. zmq端口名称
"""
SERVER_PROXY_MARKET = "server_proxy_market"
SERVER_PROXY_TRADE = "server_proxy_trade"
SERVER_PROXY_REQUEST = "server_proxy_request"

SERVICE_MANAGER_LOGIN_IN = "service_manager_login_in"
SM_LOGIN_LOCAL = "login_local_ip"
SM_LOGIN_REMOTE ="login_remote_ip"
SM_LOGIN_PORT = 'login_port'

MANAGER_BROADCAST_PORT = "manager_broadcast_port"
MANAGER_MESSAGE_PORT = "manager_message_port"


TCP_LOCAL_ADDRESS_HEAD = "tcp://*:"

ZMQ_TYPE_PULL = "pull"
ZMQ_TYPE_PUSH = "push"
ZMQ_TYPE_PUB = "pub"
ZMQ_TYPE_SUB = "sub"
ZMQ_TYPE_REQ = "req"
ZMQ_TYPE_REP = "rep"


"""
_____________________________________________________
sql语句
"""

SQLTABLE_TB_PROCESS = "tb_process"
SQL_ALIVE_PROCESS = "select * from tb_process where status=1"
SQL_ALIVE_PROCESS_IP = "select ip from tb_process where status=1"        #找到状态为1(alive)的所有ip.
SQL_ALIVE_PROCESS_NAME = "select process from tb_process where status=1" #找到状态为1(alive)的所有name.
SQL_GET_LOGIN_KEYS = "select public_key, private_key from tb_cipher where name = 'login_demo'"

TB_ORDER = "tb_order"
TB_TRADE_DETAIL = "tb_trade_detail"
TB_ORDER_CURRENT = "tb_order_current"
TB_ORDER_FINISH = "tb_order_finish"
TB_ORDER_ALL = "tb_order_all"
TB_ORDER_RECORDS = "tb_order_records"



"""
_____________________________________________________
标点符号
"""
MARK_COMMA = ","
MARK_PERIOD = "."
MARK_UNDERLINE = "_"
MARK_HYPHEN = "-"
MARK_COLON = ":"
MARK_PLUS = "+"
MARK_MINUS = "-"
MARK_QUESTIONMARK = "?"
MARK_EXCLAMATION = "!"
MARK_SEMICOLON = ";"
MARK_PARENTHESES_L = "("
MARK_PARENTHESES_R = ")"
MARK_DOLLAR = "$"
MARK_ADDRESS = "@"
MARK_EQUAL = "="
MARK_SPACE = " " # 空格
MARK_EMPTY_STRING = ""

PYTHON_EXTENSION = ".py"

"""
bitmex错误码
"""
SYSTEM_OVERLOADED = "The system is currently overloaded. Please try again later"
"""
bitmex重新下单次数
"""
PLACE_ORDER_NUM = 5
"""
错误码定义
"""
# 未定义错误
ERROR_CODE_UNKNOW_ERROR = 100000
ERROR_MSG_UNKNOW_ERROR = "unknow error"
# 秘钥不存在
ERROR_CODE_SIGN_NOT_EXIST = 114000
ERROR_MSG_SIGN_NOT_EXIST = "the sign not exist"
# 签名未通过验证
ERROR_CODE_SIGN_AUTH_INVALID = 114001
ERROR_MSG_SIGN_AUTH_INVALID = "the sign is invalid"
# 请求参数异常  例如签名验证的时候参数有误
ERROR_CODE_REQUEST_PARAM_ERROR = 114002
ERROR_MSG_REQUEST_PARAM_ERROR = "the request params is error"
# 交易所系统错误
ERROR_CODE_EXCHANGE_SYSTEM_ERROR = 133000
ERROR_MSG_EXCHANGE_SYSTEM_ERROR = "the exchange system error"
# 访问超时
ERROR_CODE_REQUEST_TIMEOUT = 133001
ERROR_MSG_REQUEST_TIMEOUT = "the request timeout"
# 访问频繁
ERROR_CODE_TOO_MANY_REQUEST = 133002
ERROR_MSG_TOO_MANY_REQUEST = "too many request"
# 交易被冻结
ERROR_CODE_TRADE_IS_FREEZE = 133003
ERROR_MSG_TRADE_IS_FREEZE = "the trade is freeze"
# 系统过载，请再试一次
ERROR_CODE_CURRENTLY_OVERLOADED = 133004
ERROR_MSG_CURRENTLY_OVERLOADED = "The system is currently overloaded. Please try again later"
# 请求的时间戳与服务器时间相差太大
ERROR_CODE_TIMESTAMP_AHEAD_OF_SERVER = 133004
ERROR_MSG_TIMESTAMP_AHEAD_OF_SERVER = "the timestamp was 1000ms ahead of the server's time"
# 请求参数有误  例如签名通过但是下单时候的参数有误，如价格为0或者量为0
ERROR_CODE_ORDER_PARAM_ERROR = 134000
ERROR_MSG_ORDER_PARAM_ERROR = "the order params is error"
# 资金不足
ERROR_CODE_BALANCE_NOT_ENOUGH = 134001
ERROR_MSG_BALANCE_NOT_ENOUGH = "the balance not enough"
# 交易对不存在
ERROR_CODE_SYMBOL_NO_EXISTS = 134002
ERROR_MSG_SYMBOL_NO_EXISTS = "the symbol no exists"
# 下单最小交易量
ERROR_CODE_MIN_VOLUME_NO_SATISFIABLE = 134003
ERROR_MSG_MIN_VOLUME_NO_SATISFIABLE = "the min volume no satisfiable"
# 订单状态错误
ERROR_CODE_ORDER_STATUS_ERROR = 134004
ERROR_MSG_ORDER_STATUS_ERROR = "the order status error"
# 下单精度有误
ERROR_CODE_OUT_OF_PRECISION_LIMIT = 134005
ERROR_MSG_OUT_OF_PRECISION_LIMIT = "the order out of precision limit"
# 下单数量为0
ERROR_CODE_VOLUME_IS_ZERO = 134006
ERROR_MSG_VOLUME_IS_ZERO = "the volume is 0"
# 撤单失败
ERROR_CODE_CANCEL_ORDER_FAILED = 134007
ERROR_MSG_CANCEL_ORDER_FAILED = "cancel order is failed"
# 券商id不存在
ERROR_CODE_SECURITIES_NOT_EXIST = 134008
ERROR_MSG_SECURITIES_NOT_EXIST = "securities id is not exist"
# 没有交易市场信息
ERROR_CODE_TRADE_MARKET_NOT_EXIST = 134009
ERROR_MSG_TRADE_MARKET_NOT_EXIST = "trade market is not exist"
# 必选参数不能为空
ERROR_CODE_REQUIRED_PARAMS_NOT_NULL = 134010
ERROR_MSG_REQUIRED_PARAMS_NOT_NULL = "required params is not null"
# 停止交易
ERROR_CODE_TRADE_IS_STOP= 134011
ERROR_MSG_TRADE_IS_STOP = "trade is stop"
# 价格发现期间您只可下市价单
ERROR_CODE_PLACE_MARKET_ORDER = 134012
ERROR_MSG_PLACE_MARKET_ORDER = "required place market order"
# 价格发现第二阶段您不可以撤单
ERROR_CODE_NOT_CANCEL_ORDER = 134013
ERROR_MSG_NOT_CANCEL_ORDER = "not required cancel order"
# 没有最新行情信息
ERROR_CODE_MARKET_NOT_MSG = 134014
ERROR_MSG_MARKET_NOT_MSG = "the market is not msg"
# 没有K线类型
ERROR_CODE_KLINE_IS_NOT_MSG = 134015
ERROR_MSG_KLINE_IS_NOT_MSG = "the kline is not msg"
# 订单不存在
ERROR_CODE_ORDER_NOT_EXIST = 1340016
ERROR_MSG_ORDER_NOT_EXIST = "the order is not exist"
# 下单失败
ERROR_CODE_PLACE_ORDER_ERROR = 1340017
ERROR_MSG_PLACE_ORDER_ERROR = "place order is error"
# 请求的新订单太多
ERROR_CODE_PLACE_ORDERS_TOO_MANY = 1340018
ERROR_MSG_PLACE_ORDERS_TOO_MANY = "place order too many"
# 期货下单价格有误
ERROR_CODE_FUTURES_PLACE_ORDERS_ERROR = 1340019
ERROR_MSG_FUTURES_PLACE_ORDERS_ERROR = "futures place order error"
# 当前订单已经成交
ERROR_CODE_ORDERS_IS_FILLED = 1340020
ERROR_MSG_ORDERS_IS_FILLED = "the order is filled"
# 当前订单已经撤销
ERROR_CODE_ORDERS_IS_CANCELED = 1340021
ERROR_MSG_ORDERS_IS_CANCELED = "the order is canceled"
# 订单总价精度问题
ERROR_CODE_AMOUNT_PRICE_ERROR = 1340022
ERROR_MSG_AMOUNT_PRICE_ERROR = "the amount price is error"


