import base64
from cdp.auth.utils.jwt import generate_jwt, JwtOptions

api_key = "26f7e5fa-0c5a-4151-85dd-f5e3a14af0f0"
api_secret = "Fp9O7lkldCYUc2Mil0isiHiOu1PHZF5+T5Padyz14D0lvnY/9NafLdp+W4cpZYB57VlTJgiKDgaJEcD05nXM+g=="

try:
    jwt_opts = JwtOptions(
        api_key_id=api_key,
        api_key_secret=api_secret,
        request_method="GET",
        request_host="api.coinbase.com",
        request_path="/api/v3/brokerage/products/BTC-USD",
        expires_in=120
    )
    token = generate_jwt(jwt_opts)
    print("JWT Generated successfully")
    
    import requests
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.get("https://api.coinbase.com/api/v3/brokerage/products/BTC-USD", headers=headers)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")

