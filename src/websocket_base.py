# -*- coding: utf-8 -*-
# @Time    : 2018/7/15 11:04
# @Author  : xnbo
# @Site    : 
# @File    : websocket_base.py
# @Software: PyCharm

import threading

class WebSocketBase(object):
    def __init__(self, service_base, url=None):
        """ Connect to the websocket and initialize data stores ."""
        self.exchange = service_base.exchange
        self.logger = service_base.logger

        if url:
            self.url = url
        else:
            self.url = service_base.ws_url
        self.on_message = service_base.on_message
        self.on_close = service_base.on_close
        self.on_open = service_base.on_open
        self.on_error = service_base.on_error
        self.ping_interval = service_base.ping_interval

        self.api_key = service_base.api_key
        self.api_secret = service_base.secret_key
        # self.service_type = service_base.service_type
        # self.ws = {}

        self.exited = False

        # self.logger.info("%s %s connecting to %s", self.exchange, self.service_type, self.url)
        
        # self.checkThread = threading.Thread(target=lambda: self.check_thread())
        # self.checkThread.daemon = True
        # self.checkThread.start()
        #
        # self.logger.info("Initialized %s %s WebSocket.", self.exchange, self.service_type)
    
    def start_check_thread(self):
        """
        启动检测线程
        :return:
        """
        check_thread = threading.Thread(target=lambda: self.check_thread())
        check_thread.daemon = True
        check_thread.start()
    
    def exit(self):
        """
            exit websocket, rewritten by derived classes
        :param msg:
        :return:
        """

    def check_thread(self):
        """
            check websocket connect status, rewritten by derived classes
        :param msg:
        :return:
        """

    def send_command(self, command):
        """
            Send a raw command, rewritten by derived classes
        :param msg:
        :return:
        """
