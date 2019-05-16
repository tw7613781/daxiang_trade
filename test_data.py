from src.data import Data
import time

if __name__ == '__main__':
    data = Data()
    try:
        while True:
            time.sleep(5)
            print(data.get_market_price())
            print(data.get_wallet_balance())
            print(data.get_excess_margin())
            print(data.get_current_qty())
            print(data.get_avg_entry_price())
    except KeyboardInterrupt:
        data.close()
