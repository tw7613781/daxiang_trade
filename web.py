'''
a http server to display system info
'''
import os
import threading
from portfolio import Portfolio
import settings as s
import utils as u
from flask import Flask
from gevent.pywsgi import WSGIServer
from time import time, sleep
from datetime import datetime as t

class Web:

    def __init__(self, portfolio):
        '''
        initial with a portfolio instance, so the web only display the portfolio info and log info
        '''
        self.p = portfolio
        self.app = Flask(__name__)
        self.register_route()
        self.start_time = t.now()
        self.start_web_server()
    
    def _start_web_server(self):
        '''
        start the web server with WSGI standard
        '''
        self.server = WSGIServer(('', 8080), self.app, log=None)
        self.server.serve_forever()
    
    def start_web_server(self):
        '''
        create a threading to host web server
        '''
        t = threading.Thread(target=self._start_web_server, args=())
        t.daemon = True
        t.start()
    
    def register_route(self):
        '''
        register route without decorator
        '''
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/log', 'log', self.log)

    def log(self):
        return u.read_log('daxiang_robot.log')
    
    def index(self):
        balance, position = self.p.portfolio_info()
        text = f'Daxiang Trading Robot - Uptime {t.now() - self.start_time} <br><hr>'
        text += f'Current Position: {position[0]}, Average Price: {position[1]} <br>'
        text += 'Profit History: <br>'
        text += '---------------------- Balance(XBT) -- Change_Rate -- Total_Change_Rate<br>'
        for b in balance:
            text += f'{b[0]}: {b[1]/100000000}, {b[2]}%, {b[3]}% <br>'
        text += '<br><hr>'
        text += 'Recent System Log: <br>'
        text += u.read_recent_log('daxiang_robot.log', -1024*10)
        text += '<hr>'
        text += 'Full System Log: <br>'
        text += u.href_wrapper('daxiang_robot.log')
        text += '<br>'
        return text