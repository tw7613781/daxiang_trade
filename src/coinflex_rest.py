"""Restful API request to coinflex
Return coinflex exchange data requested thru RESTFUL api

Author: Tang Wei <tw7613781@gmail.com>
Created: Jan 21, 2022
"""
import os
import base64
import hmac
import hashlib
import datetime
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from utils import print_error

load_dotenv()

TERM_RED   = '\033[1;31m'
TERM_NFMT  = '\033[0;0m'
TERM_BLUE  = '\033[1;34m'
TERM_GREEN = '\033[1;32m'

HOST= 'https://v2api.coinflex.com'
PATH= 'v2api.coinflex.com'
api_key = os.getenv('APIKEY')
api_secret = os.getenv('APISECRET')
nonce = 870830

def private_call(method, options={}):
  '''
  generate header based on api credential
  method: private call method
  options: parameters if have,, the format is as below
        {'key1': 'value1', 'key2': 'value2'}
  '''
  ts = datetime.datetime.utcnow().isoformat()
  body = urlencode(options)
  if options:
    path = method + '?' + body
  else:
    path = method
  msg_string = '{}\n{}\n{}\n{}\n{}\n{}'.format(ts, nonce, 'GET', PATH, method, body)
  sig = base64.b64encode(hmac.new(api_secret.encode('utf-8'), msg_string.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')

  header = {'Content-Type': 'application/json', 'AccessKey': api_key,
            'Timestamp': ts, 'Signature': sig, 'Nonce': str(nonce)}

  resp = requests.get(HOST + path, headers=header)
  return resp.json()

def isAlive() -> bool:
  "public GET /v2/ping"
  try:
    endpoint = '/v2/ping'
    response = requests.get(HOST + endpoint)
    data = response.json()
    return data['success']
  except Exception as err:
    print_error('isAlive', err)
  
def getOrderBook(market, depth):
  "get order books of specific trading market with specific depth"
  try:
    endpoint = f'/v2/depth/{market}/{depth}'
    response = requests.get(HOST + endpoint)
    return response.json()
  except Exception as err:
    print_error('getOrderBook', err)

def getBalance():
  '''
  get account balance
  '''
  try:
    endpoint = '/v2/balances'
    return(private_call(endpoint))
  except Exception as err:
    print_error('getBalance', err)    
  
def getBalanceBySymbol(symbol):
  '''
  get account balance by specific symbol
  '''
  try:
    endpoint = f'/v2/balances/{symbol}'
    return(private_call(endpoint))
  except Exception as err:
    print_error('getBalanceBySymbol', err)

def getPositions():
  '''
  get account positions
  '''
  try:
    endpoint = '/v2/positions'
    return(private_call(endpoint))
  except Exception as err:
    print_error('getPositions', err)

def getPositionsBySymbol(symbol):
  '''
  get account position by specific symbol
  '''
  try:
    endpoint = f'/v2/positions/{symbol}'
    return(private_call(endpoint))
  except Exception as err:
    print_error('getPositionsBySymbol', err)


if __name__ == '__main__':
  
  print(f'{TERM_BLUE}1. public /v2/ping{TERM_NFMT}')
  print(isAlive())

  print(f'{TERM_BLUE}2. public /v2/depth/FLEX-USD/10{TERM_NFMT}')
  print(getOrderBook('FLEX-USD', 10))

  print(f'{TERM_BLUE}3. private /v2/balances{TERM_NFMT}')
  print(getBalance())

  print(f'{TERM_BLUE}4. private /v2/balances/USD{TERM_NFMT}')
  print(getBalanceBySymbol('USD'))

  print(f'{TERM_BLUE}5. private /v2/positions{TERM_NFMT}')
  print(getPositions())

  print(f'{TERM_BLUE}6. private /v2/positions/ETH{TERM_NFMT}')
  print(getPositionsBySymbol('ETH-USD-SWAP-LIN'))
