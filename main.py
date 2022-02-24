'''
Daxiang trading robot main entry
'''
import sys
from src.coinflex_fly import CoinflexFly

if __name__ == '__main__':
  config_file = sys.argv[-1]
  if len(sys.argv) == 2:   
    coinflexFly = CoinflexFly(config_file)
    coinflexFly.websocket_app.wst.join()
    coinflexFly.websocket_app.check_thread.join()
  else:
    print("config file is not provided!")
    sys.exit()