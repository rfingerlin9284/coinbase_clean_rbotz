import os
from coinbase.rest import RESTClient

# Load env safely
env_file = '.env'
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"\'')

api_key = os.getenv("COINBASE_ECDSA_KEY_ID") or os.getenv("COINBASE_API_KEY_ID")
api_secret = os.getenv("COINBASE_ECDSA_KEY_SECRET") or os.getenv("COINBASE_API_KEY_SECRET")

if not api_key or not api_secret:
    print("❌ ERROR: COINBASE_ECDSA_KEY_ID or COINBASE_ECDSA_KEY_SECRET missing from .env")
    exit(1)

# Ensure no PEM wrapping and normalize newlines for Ed25519
api_secret = api_secret.replace("\\n", "\n")

try:
    print("Attempting Coinbase CDP Auth...")
    client = RESTClient(api_key=api_key, api_secret=api_secret)
    accounts = client.get_accounts()
    print(f"✅ Auth Success! Found {len(accounts.get('accounts', []))} accounts.")
    
    btc = client.get_product("BTC-USD")
    print(f"✅ Market Data OK! BTC-USD price: {btc.get('price')}")
except Exception as e:
    print(f"❌ Auth Failed: {e}")
