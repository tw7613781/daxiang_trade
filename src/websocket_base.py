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
        
        self.exited = False
    
    def start_check_thread(self):
        """
        启动检测线程
        :return:
        """
        self.check_thread = threading.Thread(target=lambda: self.check_thread_impl())
        self.check_thread.daemon = True
        self.check_thread.start()
    
    def exit(self):
        """
            exit websocket, rewritten by derived classes
        :param msg:
        :return:
        """

    def check_thread_impl(self):
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
