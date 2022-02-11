# -*- coding: utf-8 -*-
# @Time    : 2018/8/07 16:21
# @Author  : zxlong
# @Site    :
# @File    : huobi_utils.py
# @Software: PyCharm

from common.constant import *


class HuobiUtils:
	# 交易所返回的订单状态
	HUOBI_STATE_PRE_SUBMITTED = 'pre-submitted'  # 准备提交
	HUOBI_STATE_SUBMITTING = 'submitting'  # 提交中
	HUOBI_STATE_SUBMITTED = 'submitted'  # 已提交
	HUOBI_STATE_PARTIAL_FILLED = 'partial-filled'  # 部分成交
	HUOBI_STATE_PARTIAL_CANCELED = 'partial-canceled'  # 部分成交撤销
	HUOBI_STATE_FILLED = 'filled'  # 完全成交
	HUOBI_STATE_CANCELED = 'canceled'  # 已撤销

	'''balance type in huobi'''
	HUOBI_BALANCE_TYPE_TRADE = 'trade'
	HUOBI_BALANCE_TYPE_FROZEN = 'frozen'

	"""huobi下单接口调用状态"""
	API_RSP_STATUS_OK = 'ok'

	PRICE_TYPE_IOC = 'ioc'

	@staticmethod
	def generate_sub_id(service_type, sub_id=0):
		"""
		生成订阅channel的ID
		:param service_type: trade or market
		:param sub_id: 自然数，建议是顺序增长
		:return:
		"""
		return service_type + '%s' % sub_id

	@staticmethod
	def convert_order_state(order_state):
		"""
		订单状态转换
		:param order_state:
		:return:
		"""
		int_state = ORDER_STATE_UNKNOWN
		if order_state == HuobiUtils.HUOBI_STATE_PRE_SUBMITTED:
			int_state = ORDER_STATE_PRE_SUBMITTED
		elif order_state == HuobiUtils.HUOBI_STATE_SUBMITTING:
			int_state = ORDER_STATE_SUBMITTING
		elif order_state == HuobiUtils.HUOBI_STATE_SUBMITTED:
			int_state = ORDER_STATE_SUBMITTED
		elif order_state == HuobiUtils.HUOBI_STATE_PARTIAL_FILLED:
			int_state = ORDER_STATE_PARTIAL_FILLED
		elif order_state == HuobiUtils.HUOBI_STATE_PARTIAL_CANCELED:
			int_state = ORDER_STATE_PARTIAL_CANCELED
		elif order_state == HuobiUtils.HUOBI_STATE_FILLED:
			int_state = ORDER_STATE_FILLED
		elif order_state == HuobiUtils.HUOBI_STATE_CANCELED:
			int_state = ORDER_STATE_CANCELED

		return int_state

	@staticmethod
	def is_market(trade_type):
		if trade_type:
			return trade_type.find(SERVICE_MARKET) >= 0

	@staticmethod
	def is_limit(trade_type):
		if trade_type:
			return trade_type.find(LIMIT) >= 0

	@staticmethod
	def is_ioc(trade_type):
		if trade_type:
			return trade_type.find(HuobiUtils.PRICE_TYPE_IOC) >= 0

	@staticmethod
	def is_sell(trade_type):
		if trade_type:
			return trade_type.find(SELL) >= 0

	@staticmethod
	def is_buy(trade_type):
		if trade_type:
			return trade_type.find(BUY) >= 0

	@staticmethod
	def get_direction(trade_type):
		""""
		 获取订单的买卖方向，根据trade_type中是否包含"buy"或"sell"进行判断
		"""
		if HuobiUtils.is_buy(trade_type):
			return BUY
		elif HuobiUtils.is_sell(trade_type):
			return SELL
		else:
			return ''

	@staticmethod
	def get_price_type(trade_type):
		""""
		获取订单的价格类型，根据trade_type中是否包含"limit"或"market"或"ioc"进行判断
		"""
		if HuobiUtils.is_market(trade_type):
			return SERVICE_MARKET
		elif HuobiUtils.is_limit(trade_type):
			return LIMIT
		elif HuobiUtils.is_ioc(trade_type):
			return HuobiUtils.PRICE_TYPE_IOC
		else:
			return ''
	@staticmethod
	def convert_error_code(rsp={}):
		# error_code = int(rsp.get("err-code", 100000))
		error_msg = rsp.get("err-msg", "")
		if "base-symbol-error" in error_msg: # 交易对不存在
			code = ERROR_CODE_SYMBOL_NO_EXISTS
			msg = ERROR_MSG_SYMBOL_NO_EXISTS
		elif "base-date-error" in error_msg: # 错误的日期格式
			code = ERROR_CODE_REQUEST_PARAM_ERROR
			msg = ERROR_MSG_REQUEST_PARAM_ERROR
		elif "account-transfer-balance-insufficient-error" in error_msg: # 余额不足无法冻结
			code = ERROR_CODE_BALANCE_NOT_ENOUGH
			msg = ERROR_MSG_BALANCE_NOT_ENOUGH
		elif "bad-argument" in error_msg: # 无效参数
			code = ERROR_CODE_ORDER_PARAM_ERROR
			msg = ERROR_MSG_ORDER_PARAM_ERROR
		elif "api-signature-not-valid" in error_msg: # API签名错误
			code = ERROR_CODE_SIGN_AUTH_INVALID
			msg = ERROR_MSG_SIGN_AUTH_INVALID
		elif "gateway-internal-error" in error_msg: # 系统繁忙，请稍后再试
			code = ERROR_CODE_EXCHANGE_SYSTEM_ERROR
			msg = ERROR_MSG_EXCHANGE_SYSTEM_ERROR
		elif "security-require-assets-password" in error_msg: # 需要输入资金密码
			code = ERROR_CODE_REQUEST_PARAM_ERROR
			msg = ERROR_MSG_REQUEST_PARAM_ERROR
		elif "audit-failed" in error_msg: # 下单失败
			code = ERROR_CODE_PLACE_ORDER_ERROR
			msg = ERROR_MSG_PLACE_ORDER_ERROR
		elif "order-accountbalance-error" in error_msg: # 账户余额不足
			code = ERROR_CODE_BALANCE_NOT_ENOUGH
			msg = ERROR_MSG_BALANCE_NOT_ENOUGH
		elif "order-limitorder-price-error" in error_msg: # 限价单下单价格超出限制
			code = ERROR_CODE_ORDER_PARAM_ERROR
			msg = ERROR_MSG_ORDER_PARAM_ERROR
		elif "order-limitorder-amount-error" in error_msg: # 限价单下单数量超出限制
			code = ERROR_CODE_ORDER_PARAM_ERROR
			msg = ERROR_MSG_ORDER_PARAM_ERROR
		elif "order-orderprice-precision-error" in error_msg: # 下单价格超出精度限制
			code = ERROR_CODE_OUT_OF_PRECISION_LIMIT
			msg = ERROR_MSG_OUT_OF_PRECISION_LIMIT
		elif "order-orderamount-precision-error" in error_msg:
			code = ERROR_CODE_SYMBOL_NO_EXISTS
			msg = ERROR_MSG_SYMBOL_NO_EXISTS
		elif "order-queryorder-invalid" in error_msg: # 查询不到此条订单
			code = ERROR_CODE_ORDER_NOT_EXIST
			msg = ERROR_MSG_ORDER_NOT_EXIST
		elif "order-orderstate-error" in error_msg: # 订单状态错误
			code = ERROR_CODE_ORDER_STATUS_ERROR
			msg = ERROR_MSG_ORDER_STATUS_ERROR
		elif "order-datelimit-error" in error_msg: # 查询超出时间限制
			code = ERROR_CODE_TIMESTAMP_AHEAD_OF_SERVER
			msg = ERROR_MSG_TIMESTAMP_AHEAD_OF_SERVER
		elif "order-update-error" in error_msg: # 订单更新出错
			code = ERROR_CODE_ORDER_STATUS_ERROR
			msg = ERROR_MSG_ORDER_STATUS_ERROR
		else:
			code = ERROR_CODE_UNKNOW_ERROR
			msg = ERROR_MSG_UNKNOW_ERROR

		return code, msg


