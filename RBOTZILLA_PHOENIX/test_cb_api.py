import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("COINBASE_LIVE_API_KEY")
api_secret = os.getenv("COINBASE_LIVE_API_SECRET")

import base64
print(f"Key: {api_key}")
print(f"Secret lines: {len(api_secret.split('\\n'))}")

from cdp.auth.utils.jwt import generate_jwt, JwtOptions
import json

from urllib.parse import urlparse

def test_api():
    try:
        # Replicate logic in coinbase_connector.py
        request_method = "GET"
        endpoint = "https://api.coinbase.com/api/v3/brokerage/products/BTC-USD"
        parsed = urlparse(endpoint)
        path = parsed.path
        host = parsed.netloc

        key_data = api_secret
        if "\\n" in key_data:
            key_data = key_data.replace("\\n", "\n")

        if "BEGIN EC PRIVATE KEY" not in key_data:
            key_data = f"-----BEGIN EC PRIVATE KEY-----\n{key_data.strip()}\n-----END EC PRIVATE KEY-----\n"

        jwt_opts = JwtOptions(
            api_key_id=api_key,
            api_key_secret=key_data,
            request_method=request_method,
            request_host=host,
            request_path=path,
            expires_in=120
        )

        token = generate_jwt(jwt_opts)
        print("JWT Generated successfully")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        r = requests.get(endpoint, headers=headers)
        print(f"Status: {r.status_code}")
        print(r.text[:200])
        
    except Exception as e:
        print(f"Error: {e}")

test_api()
