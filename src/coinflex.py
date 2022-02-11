from os import path
import threading
from datetime import datetime
from src.websocket_app import MyWebSocketApp
from src.common.global_utils import *

class Coinflex():

  def __init__(self, config_file):    
    self.exchange = "CoinFLEX"
    self.init_finish_event = threading.Event()  # 用来控制服务初始化完成才处理请求

    # self.con_file = path.join(path.split(path.realpath(__file__))[0], config_file)
    self.con_file = config_file

    self.ws_url = get_json_config(file=self.con_file, section=self.exchange, key="WSURL")
    self.account_id = get_json_config(file=self.con_file, section=self.exchange, key="USERID")
    self.api_key = get_json_config(file=self.con_file, section=self.exchange, key="APIKEY")
    self.secret_key = get_json_config(file=self.con_file, section=self.exchange, key="APISECRET")
    
    self.ping_interval = 5
    
    self.logger = setup_logger(self.account_id + "_" + self.exchange + "_" + datetime.datetime.now().strftime("%m%d%Y%H%M%S"), log_path="./logs")

    self.websocket_app = MyWebSocketApp(self)
    
    self.init_finish_event.set()

  def on_message(self, msg, ws=None):
      """
		  处理websocket的market数据
		  :param msg:
		  :return:
	  	"""
      try:
        self.logger.info("ON_MESSAGE={}".format(msg))
        # msg = gzip.decompress(msg).decode('utf-8')
        # msg = json.loads(msg)
        # if 'ping' in msg:
          # pong = {"pong": msg['ping']}
          # self.webscoket_app.send_command(json.dumps(pong))
          # return
      except:
        self.logger.error("on_message error!  %s " % msg)
        self.logger.error(traceback.format_exc())

  def on_error(self, error):
      """ Called on fatal websocket errors. We exit on these. """
      try:
        self.logger.error("%s __on_error : %s", self.exchange, error)
      except:
        self.logger.error("on_error Error!!!")
        self.logger.error(traceback.format_exc())

  def on_open(self):
      """ Called when the WS opens. """
      try:
        self.logger.info("%s websocket opened.", self.exchange)
        ## subscribe msg sent
      except:
        self.logger.error("on_open Error!!!")
        self.logger.error(traceback.format_exc())

  def on_close(self):
      """ Called on websocket close."""
      try:
        self.logger.info("%s websocket closed.", self.exchange)
      except:
        self.logger.error("on_close Error!!!")
        self.logger.error(traceback.format_exc())