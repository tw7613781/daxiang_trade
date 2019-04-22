import bitmex
import settings as s

client = bitmex.bitmex(api_key=s.API_KEY, api_secret=s.API_SECRET)

data = client.Trade.Trade_getBucketed(
    binSize = '5m',
    symbol='XBTUSD',
    count=100,
    reverse=True
).result()