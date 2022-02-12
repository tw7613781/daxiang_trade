'''
Daxiang trading robot main entry
'''
import sys
from src.coinflex import Coinflex

if __name__ == '__main__':
  config_file = sys.argv[-1]
  if len(sys.argv) == 2:   
    coinflex = Coinflex(config_file)
    coinflex.websocket_app.wst.join()
    coinflex.websocket_app.check_thread.join()
  else:
    print("config file is not provided!")
    sys.exit()