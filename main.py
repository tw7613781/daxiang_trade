'''
Daxiang trading robot main entry and a http server to display system info
'''
import os
import threading
from portfolio import Portfolio
import settings as s
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
        self.server = WSGIServer(('127.0.0.1', 8080), self.app, log=None)
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
    
    def index(self):
        balance, position = self.p.portfolio_info()
        text = f'Daxiang Trading Robot - Uptime {t.now() - self.start_time} <br><hr>'
        text += f'Current Position: {position[0]}, Average Price: {position[1]} <br>'
        text += 'Profit History: <br>'
        text += '---------------------- Balance(XBT) -- Rate <br>'
        for b in balance:
            text += f'{b[0]}: {b[1]/100000000}, {b[2]*100}% <br>'
        text += '<br><hr>'
        text += 'Recent System Log: <br>'
        with open('log/daxiang_robot.log', 'r') as f:
            line = f.readline()
            text += line
            text += '<br>'
            while line:
                line = f.readline()
                text += line
                text += '<br>'
        text += '<hr>'
        text += 'History System Log: <br>'
        for file in os.listdir('log'):
            if file.endswith(".log"):
                text += os.path.join("log", file)
                text += '<br>'
        return text

if __name__ == '__main__':
    main = Main()
    main.start_web_server()
    while True:
        if round(time()) % s.INTERVAL[s.BIN_SIZE] == 1:
            main.p.run()
        sleep(0.5)

    


    
