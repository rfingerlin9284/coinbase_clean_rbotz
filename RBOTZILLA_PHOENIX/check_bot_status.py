#!/usr/bin/env python3
"""
Bot Status Checker - Knows if bot is trading or not
Shows real-time bot awareness and trading status
"""

import sys
import subprocess
import json
import time
from pathlib import Path

def get_bot_process_status():
    """Check if bot process is running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'oanda_trading_engine.py'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def check_narration_logs():
    """Check recent narration logs for trading activity"""
    try:
        narration_file = Path('/home/rfing/RBOTZILLA_PHOENIX/narration.jsonl')
        if not narration_file.exists():
            return None
        
        # Read last 50 lines
        with open(narration_file, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return None
        
        recent_lines = lines[-50:]
        
        # Look for recent trade events
        trade_events = []
        for line in recent_lines:
            try:
                event = json.loads(line)
                if event.get('event_type') in ['TRADE_PLACED', 'POSITION_OPENED', 'POSITION_CLOSED', 'TRADE_RESULT']:
                    trade_events.append({
                        'timestamp': event.get('timestamp', '')[:19],
                        'event': event.get('event_type'),
                        'symbol': event.get('symbol', '')
                    })
            except:
                pass
        
        return trade_events if trade_events else None
    except Exception as e:
        return None

def get_open_positions():
    """Check for open positions via OANDA API"""
    try:
        import os
        from brokers.oanda_connector import OandaConnector
        
        token = os.getenv('OANDA_PRACTICE_TOKEN')
        account_id = os.getenv('OANDA_PRACTICE_ACCOUNT_ID')
        
        if not token or not account_id:
            return None
        
        connector = OandaConnector(environment='practice')
        trades = connector.get_trades()
        
        if trades:
            return [{'symbol': t.get('instrument'), 'units': t.get('initialUnits')} for t in trades]
        return None
    except Exception as e:
        return None

def main():
    print("\n" + "="*80)
    print("🤖 BOT STATUS AWARENESS CHECK")
    print("="*80 + "\n")
    
    # Check 1: Process status
    print("1️⃣  PROCESS STATUS:")
    print("-" * 80)
    is_running = get_bot_process_status()
    if is_running:
        print("  ✅ Bot process: RUNNING")
    else:
        print("  ❌ Bot process: STOPPED")
    
    # Check 2: Recent trading activity
    print("\n2️⃣  RECENT TRADING ACTIVITY:")
    print("-" * 80)
    trades = check_narration_logs()
    if trades:
        print(f"  Found {len(trades)} recent trade events:")
        for trade in trades[-5:]:
            print(f"     • {trade['timestamp']} {trade['event']:20} {trade['symbol']}")
    else:
        print("  ⚠️  No recent trades found")
    
    # Check 3: Open positions
    print("\n3️⃣  OPEN POSITIONS:")
    print("-" * 80)
    positions = get_open_positions()
    if positions:
        print(f"  🟢 ACTIVELY TRADING with {len(positions)} open position(s):")
        for pos in positions:
            print(f"     • {pos['symbol']}: {pos['units']} units")
    else:
        print("  🟡 No open positions (scanning for signals or idle)")
    
    # Final status
    print("\n" + "="*80)
    print("📊 BOT AWARENESS:")
    print("="*80)
    
    if is_running and positions:
        print("\n  🟢 BOT IS ACTIVELY TRADING")
        print(f"     • Process: RUNNING")
        print(f"     • Positions: {len(positions)} open")
        print(f"     • Status: TRADING LIVE")
        status_code = 0
    elif is_running:
        print("\n  🟡 BOT IS RUNNING (but not trading)")
        print(f"     • Process: RUNNING")
        print(f"     • Positions: 0 open")
        print(f"     • Status: SCANNING FOR SIGNALS")
        status_code = 1
    else:
        print("\n  🔴 BOT IS STOPPED")
        print(f"     • Process: STOPPED")
        print(f"     • Positions: Unknown")
        print(f"     • Status: NOT RUNNING")
        status_code = 2
    
    print("\n" + "="*80 + "\n")
    
    return status_code

if __name__ == "__main__":
    sys.exit(main())
