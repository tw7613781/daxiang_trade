# -*- coding: utf-8 -*-
# @Time    : 2018/7/18 21:42
# @Author  : xnbo
# @Site    : 
# @File    : websocket_app.py
# @Software: PyCharm

import ssl
import threading
import websocket
import traceback
from time import sleep
from src.websocket_base import WebSocketBase

class MyWebSocketApp(WebSocketBase):
    def __init__(self, service_base, header=None):
        super(MyWebSocketApp, self).__init__(service_base)
        self.header = header
        self.service_base = service_base

        self.exited = False  # 为false不启动重新检测

        self.ws = None
        self.connect(self.url)
        # 启动检测线程
        self.start_check_thread()

    def exit(self):
        self.exited = True
        self.ws.close()

    def check_thread(self):
        while True:
            try:
                if (not self.ws.sock or not self.ws.sock.connected) and self.exited:
                    if self.ws.sock:
                        self.ws.close()
                    self.logger.info("%s reconnecting to %s", self.exchange, self.url)
                    self.connect(self.url)
                else:
                    sleep(1)
            except:
                self.logger.error(traceback.print_exc())

    def connect(self, url):
        """ Connect to the websocket in a thread."""
        try:
            self.exited = True
            self.ws = websocket.WebSocketApp(url,
                                             on_message=self.__on_message,
                                             on_close=self.__on_close,
                                             on_open=self.__on_open,
                                             on_error=self.__on_error,
                                             header=self.header)
            if self.exchange.lower() == "bitmex":
                ssl_defaults = ssl.get_default_verify_paths()
                sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
                self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
            else:
                self.wst = threading.Thread(target=lambda: self.ws.run_forever(ping_interval=self.ping_interval))
            self.wst.daemon = True
            self.wst.start()
            self.logger.info("%s websocket run_forever thread started", self.exchange)

            # Wait for connect before continuing
            conn_timeout = 10
            while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
                sleep(1)
                conn_timeout -= 1
            if not conn_timeout:
                self.logger.error("%s couldn't connect to WS! Exiting.", self.exchange)
                # self.exit()
                self.ws.close()
            else:
                self.logger.info('Connected to %s WS.', self.exchange)
        except:
            self.logger.error("%s couldn't connect to WS! Exiting.", self.exchange)
            self.logger.error(traceback.print_exc())

    def send_command(self, command):
        """ Send a raw command."""
        if self.service_base.init_finish_event.wait():
            self.ws.send(command)

    def __on_message(self, ws, message):
        if self.service_base.init_finish_event.wait():
            self.on_message(message, ws)

    def __on_error(self, ws, error):
        if self.service_base.init_finish_event.wait():
            self.on_error(error)

    def __on_open(self, ws):
        if self.service_base.init_finish_event.wait():
            self.on_open()

    def __on_close(self, ws):
        if self.service_base.init_finish_event.wait():
            self.on_close()
