import os
import requests
import time
import hmac
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("COINBASE_LIVE_API_KEY")
api_secret = os.getenv("COINBASE_LIVE_API_SECRET")

# Remove PEM headers if they were added
api_secret = api_secret.replace("-----BEGIN EC PRIVATE KEY-----\\n", "").replace("\\n-----END EC PRIVATE KEY-----\\n", "")

def test_legacy_hmac():
    method = "GET"
    request_path = "/api/v3/brokerage/products/BTC-USD"
    body = ""
    timestamp = str(int(time.time()))
    
    message = timestamp + method + request_path + body
    
    try:
        decoded_secret = base64.b64decode(api_secret)
        signature = hmac.new(decoded_secret, message.encode('utf-8'), hashlib.sha256).hexdigest()
        
        headers = {
            "CB-ACCESS-KEY": api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.get("https://api.coinbase.com" + request_path, headers=headers)
        print(f"Status: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Error: {e}")

test_legacy_hmac()
