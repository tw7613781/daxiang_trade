## Daxiang Trading Robot - a auto trading system for Bitmex   

[demo](http://52.78.117.239/)

## Disclaimer    

The project is only for study purpose, nothing contained in the Site constitutes investment, legal or tax advice. Neither the information nor any opinion contained in the Site constitutes a solicitation or an offer to buy or sell any securities, futures, options or other financial instruments. Decisions based on information contained on this site are the sole responsibility of the visitor.

## Introduction    

- Simple strategy, robust system, plus risk management are the three characteristics of Daxiang trading robot.      
- Adopting design pattern of parameterization and modularity, which means it's easier to control and scale up the system.      
- Supports backtesting and a simple dashboard.   

## System code structure

The main structure is consist of blew 4 files in src directory:  
- data: talk with Bitbix restful API and websocket. Fetch ohlcv data source and give orders. 
- strategy: give a signal (buy, sell, nothing) based on data source .
- portfolio: manage the account's portfolio. give exact amount of order base on strategy.
- web: provide a dashboard to display the portfolio performance    

The other files
- main: the system entry point
- settings: control the system by params     

For more info, please read [system modularity](https://github.com/tw7613781/daxiang_trade/wiki/system-modularity)

## How to run the system  

```python
python3 main.py
```

## Available strategy
- [MACD](https://github.com/tw7613781/daxiang_trade/blob/master/src/strategy.py)   
- [RSI](https://github.com/tw7613781/daxiang_trade/blob/master/src/strategy.py)

## Dependencies
All python dependencies is in [requirements.txt](https://github.com/tw7613781/daxiang_trade/blob/master/requirements.txt)
```python
pip3 install -r requirements.txt
```

## Running in AWS
As the WSGI server is already be used in the code about flask server, we only need a reverse web server to handle http request from public and direct to our WSGI server, which is provide by gevent.pywsgi   

we use nginx as the reverse web server

1. install nginx 
```shell
// update apt repo
sudo apt update
// install nginx
sudo apt install nginx
// check status
sudo service nginx status
```

2. Create a configuration file to direct http request to our dashboard
```conf
// make a configure file at /etc/nginx/conf.d/virtual.conf
// be aware of that the 8080 port is the port your WSGI server listening to
server {
    listen       80;
    server_name  your_public_ip or your_domain_name;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

3. Restart nginx server
```shell
sudo service nginx restart
```

Now it's able to check out the dashboard at your aws ec2 instance public address. Be aware of opening your 80 port in the aws ec2 instance.

## Notes   
Special thanks for project [ebisu](https://github.com/noda-sin/ebisu), Bitmex sample project [sample-market-maker](https://github.com/BitMEX/sample-market-maker) and Bitmex [connector](https://github.com/BitMEX/api-connectors), I studied a lot from these projects.

## TO-DOs:
- Change current poll way of fetching ohlcv data to bitmex-websocket. The way is more stable and not easy for http error, and it's more time sentitive.
- Backtest function
- More strateges