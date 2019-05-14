########################################################################################################################
# Connection/Auth
########################################################################################################################

# Testnet: "https://testnet.bitmex.com/api/v1/"
# Live Network: "https://www.bitmex.com/api/v1/"
# TEST = True --> use Testnet, TEST = False --> use Live Network
TEST= True

# The BitMEX API requires permanent API keys. Go to https://testnet.bitmex.com/app/apiKeys or https://www.bitmex.com/app/apiKeys to fill these out.
API_KEY = "faQczjkhb9UQ5nv09KTjyTRQ"
API_SECRET = "God1eB-ywL0CfhXwflkyfcB9z7XV36sbwss_JkEvf1RQqF2E"

# web info for dashboard
# put your host public ip and port here, such as: '52.78.117.239'
DASHBOARD_HOST = '127.0.0.1' 
DASHBOARD_PORT = 8080

########################################################################################################################
# Target
########################################################################################################################

# Instrument.
SYMBOL = "XBTUSD"
# Candle interval for ohlcv data
# Available size:'1m','5m','1h','1d'
BIN_SIZE = "1m"
# Interval
INTERVAL = {
    '1m': 1 * 60,
    '5m': 5 * 60,
    '1h': 60 * 60,
    '1d': 24 * 60 * 60
    }
# Websocket
NAME_WS = {
    '1m': 'tradeBin1m',
    '5m': 'tradeBin5m',
    '1h': 'tradeBin1h',
    '1d': 'tradeBin1d'   
}
# Leverage x
LEVERAGE= 5
# rate = order amount / total balance
RATE = 0.5

########################################################################################################################
# Others
########################################################################################################################

# Logging Level
# CRITICAL, ERROR, WARNING, INFO, DEBUG
LOG_LEVEL = 'DEBUG'