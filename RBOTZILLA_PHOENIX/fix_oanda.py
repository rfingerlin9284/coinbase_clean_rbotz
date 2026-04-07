import sys

with open('oanda_trading_engine.py', 'r') as f:
    content = f.read()

# Fix 1: local import of get_usd_notional
target_1 = """                            try:
                                from util.usd_converter import get_usd_notional
                                h_notional = get_usd_notional(abs(hedge_units), hedge_position.symbol, h_entry, self.oanda) or (abs(hedge_units) * h_entry)
"""
replacement_1 = """                            try:
                                h_notional = get_usd_notional(abs(hedge_units), hedge_position.symbol, h_entry, self.oanda) or (abs(hedge_units) * h_entry)
"""
if target_1 in content:
    content = content.replace(target_1, replacement_1)
    print("Fixed Fix 1")
else:
    print("Fix 1 target not found. Checking if it's already fixed.")

# Fix 2: Move the if __name__ == "__main__": asyncio.run(main()) to the bottom
target_2 = """if __name__ == "__main__":
    asyncio.run(main())

# ===== RBOTZILLA: POSITION POLICE (immutable min-notional) ====="""

replacement_2 = """# ===== RBOTZILLA: POSITION POLICE (immutable min-notional) ====="""

if target_2 in content:
    content = content.replace(target_2, replacement_2)
    # Append to the end
    content += "\nif __name__ == '__main__':\n    asyncio.run(main())\n"
    print("Fixed Fix 2")
else:
    print("Fix 2 target not found")

with open('oanda_trading_engine.py', 'w') as f:
    f.write(content)
