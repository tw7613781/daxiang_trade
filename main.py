'''
Daxiang trading robot main entry
'''
import sys
import argparse
from src.coinflex_flypig import CoinflexFlypig
from src.coinflex_turtle import CoinflexTurtle

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("strategy", help="Stratege to run")
  parser.add_argument("config", help="Config file for the stratege")
  args = parser.parse_args()
  
  strategy = args.strategy
  config_file = args.config

  if strategy == "flypig":
    coinflexFlypig = CoinflexFlypig(config_file)
    coinflexFlypig.websocket_app.wst.join()
    coinflexFlypig.websocket_app.check_thread.join()
  
  elif strategy == "turtle":
    coinflexTurtle = CoinflexTurtle(config_file)
    coinflexTurtle.websocket_app.wst.join()
    coinflexTurtle.websocket_app.check_thread.join()