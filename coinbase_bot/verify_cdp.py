#!/usr/bin/env python3
"""
Coinbase CDP API Key Verifier — RBOTzilla
Tests the SINGLE ECDSA key defined in .env and reports connection status.
"""
import os
import sys
import time

# ── Load .env ──────────────────────────────────────────────────────
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip('"\'')

# ── Read credentials ──────────────────────────────────────────────
api_key = os.getenv("COINBASE_API_KEY")
api_secret = os.getenv("COINBASE_API_SECRET")

print("\n" + "=" * 60)
print("  COINBASE CDP API KEY DIAGNOSTIC")
print("=" * 60)

if not api_key:
    print("\n❌ COINBASE_API_KEY is MISSING from .env")
    print("   → Go to: https://portal.cdp.coinbase.com/projects/api-keys")
    print("   → Create an ECDSA key with 'Advanced Trade' permissions")
    sys.exit(1)

if not api_secret:
    print("\n❌ COINBASE_API_SECRET is MISSING from .env")
    sys.exit(1)

# Validate key format
is_cdp_format = api_key.startswith("organizations/")
is_ec_pem = "BEGIN EC PRIVATE KEY" in api_secret

print(f"\n  API Key:       {api_key[:40]}...")
print(f"  Key Format:    {'✅ CDP (organizations/...)' if is_cdp_format else '❌ Legacy UUID — WRONG FORMAT'}")
print(f"  Secret Format: {'✅ EC PEM (ECDSA)' if is_ec_pem else '❌ Not an EC PEM key'}")

if not is_cdp_format:
    print("\n🚨 Your COINBASE_API_KEY is a legacy UUID, not a CDP key.")
    print("   The SDK requires the organizations/... format.")
    print("   → Go to: https://portal.cdp.coinbase.com/projects/api-keys")
    sys.exit(1)

if not is_ec_pem:
    print("\n🚨 Your COINBASE_API_SECRET is not an ECDSA PEM key.")
    print("   It should start with '-----BEGIN EC PRIVATE KEY-----'")
    print("   → Regenerate your key with ECDSA algorithm selected")
    sys.exit(1)

# ── Test connection ───────────────────────────────────────────────
print("\n  Testing connection...")
secret_formatted = api_secret.replace("\\n", "\n")

try:
    from coinbase.rest import RESTClient
except ImportError:
    print("\n❌ coinbase-advanced-py is NOT installed.")
    print("   Run: pip install coinbase-advanced-py")
    sys.exit(1)

try:
    t0 = time.time()
    client = RESTClient(api_key=api_key, api_secret=secret_formatted)
    accounts = client.get_accounts()
    latency = (time.time() - t0) * 1000
    
    acct_list = accounts.accounts if hasattr(accounts, "accounts") else accounts.get('accounts', [])
    
    print(f"\n  ✅ AUTH SUCCESS  ({latency:.0f}ms)")
    print(f"  Accounts found: {len(acct_list)}")
    
    # Show balances
    print("\n  Account Balances:")
    print("  " + "-" * 45)
    for a in acct_list:
        curr = getattr(a, "currency", a.get("currency")) if hasattr(a, "get") else a.currency
        avail = getattr(a, "available_balance", a.get("available_balance", {})) if hasattr(a, "get") else getattr(a, "available_balance", None)
        val = getattr(avail, "value", avail.get("value", "0")) if hasattr(avail, "get") else (avail.value if avail else "0")
        val_f = float(val)
        if val_f > 0.0001:  # Only show non-zero balances
            print(f"  {curr:>8s}: {val_f:>15.6f}")
    
    # Test product listing
    print("\n  Testing market data access...")
    try:
        btc = client.get_product(product_id="BTC-USD")
        px = getattr(btc, 'price', btc.get('price', 'N/A')) if hasattr(btc, 'get') else btc.price
        print(f"  ✅ BTC-USD price: ${float(px):,.2f}")
    except Exception as e:
        print(f"  ⚠️  Product fetch error: {e}")
    
    # Test futures access
    print("\n  Testing futures/perpetuals access...")
    try:
        products = client.get_products(product_type="FUTURE")
        prod_list = products.products if hasattr(products, "products") else products.get("products", [])
        if prod_list:
            print(f"  ✅ Futures products available: {len(prod_list)}")
            for p in prod_list[:3]:
                pid = getattr(p, "product_id", p.get("product_id", "")) if hasattr(p, "get") else p.product_id
                print(f"      → {pid}")
        else:
            print("  ⚠️  No futures products found (may require eligibility / region)")
    except Exception as e:
        print(f"  ⚠️  Futures access error: {e}")
    
    print("\n" + "=" * 60)
    print("  ALL CHECKS PASSED — BOT IS READY TO CONNECT")
    print("=" * 60 + "\n")

except Exception as e:
    print(f"\n  ❌ AUTH FAILED: {e}")
    print("\n  Possible causes:")
    print("  1. Key was deleted/revoked on CDP portal")
    print("  2. IP allowlist blocking this machine")
    print("  3. Key doesn't have 'Advanced Trade' permission")
    print("  4. Key was created with ED25519 instead of ECDSA")
    print(f"\n  → Go to: https://portal.cdp.coinbase.com/projects/api-keys")
    print("  → Delete and recreate with ECDSA + Advanced Trade permissions")
    sys.exit(1)
