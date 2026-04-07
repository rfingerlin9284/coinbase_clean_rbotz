#!/usr/bin/env python3
import json
import os

key_file = 'cdp_api_key.json'

target_env = '.env'

try:
    with open(key_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    name = data.get('name')
    private_key = data.get('privateKey')
    
    if not name or not private_key:
        print("❌ Invalid format in cdp_api_key.json")
        exit(1)
        
    # Safely escape literal actual newlines to exactly match Python CDP string parsers
    safe_private_key = private_key.replace('\n', '\\n')
    
    with open(target_env, 'a', encoding='utf-8') as env_f:
        env_f.write(f'\n# Auto-imported from cdp_api_key.json\n')
        env_f.write(f'COINBASE_ECDSA_KEY_ID="{name}"\n')
        env_f.write(f'COINBASE_ECDSA_KEY_SECRET="{safe_private_key}"\n')
        
    print("✅ Successfully injected key directly into .env!")
    
except FileNotFoundError:
    print(f"❌ Could not find {key_file} in {os.getcwd()}")
    print("Please drag the cdp_api_key.json you downloaded from Coinbase into this folder first!")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
