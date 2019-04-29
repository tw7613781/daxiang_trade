'''
Daxiang trading robot main entry and a http server to display system info
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

class Main():

    def __init__(self):
        self.p = Portfolio()
        self.app = Flask(__name__)
        self.register_route()
        self.start_time = t.now()
    
    def _start_web_server(self):
        self.server = WSGIServer((s.DASHBOARD_HOST, s.DASHBOARD_PORT), self.app, log=None)
        self.server.serve_forever()
    
    def start_web_server(self):
        t = threading.Thread(target=self._start_web_server, args=())
        t.daemon = True
        t.start()
    
    def register_route(self):
        '''
        register route without decorator
        '''
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/log/<name>', 'log', self.log)

    def log(self, name):
        return u.read_log(f'log/{name}')
    
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
        text += u.read_log('log/daxiang_robot.log')
        text += '<hr>'
        text += 'History System Log: <br>'
        for file in os.listdir('log'):
            if file.startswith("daxiang_robot"):
                text += u.href_wrapper(file)
                text += '<br>'
        return text

if __name__ == '__main__':
    main = Main()
    main.start_web_server()
    while True:
        if round(time()) % s.INTERVAL[s.BIN_SIZE] == 1:
            main.p.run()
        sleep(0.5)