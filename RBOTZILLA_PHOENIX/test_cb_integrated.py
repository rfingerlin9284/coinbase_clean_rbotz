import os
from brokers.coinbase_connector import CoinbaseConnector
try:
    c = CoinbaseConnector(environment='live')
    result = c.get_price("BTC-USD")
    print(f"Coinbase ping result: {result}")
except Exception as e:
    print(f"Coinbase error: {e}")
