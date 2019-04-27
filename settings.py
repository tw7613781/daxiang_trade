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

########################################################################################################################
# Target
########################################################################################################################

# Instrument.
SYMBOL = "XBTUSD"
# Candle interval for ohlcv data
BIN_SIZE = "1m"
# Interval
INTERVAL = {
    '1m': 1 * 60,
    '5m': 5 * 60,
    '1h': 60 * 60,
    '1d': 24 * 60 * 60
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
LOG_LEVEL = 'INFO'