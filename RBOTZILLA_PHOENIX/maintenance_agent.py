#!/usr/bin/env python3
"""
MAINTENANCE AGENT (DAEMON)
Purpose: Runs in the background independently from the trading engine.
1. Monitors oanda_headless.log and engine crashes.
2. Triggers an SMS alert using util/sms_client if it hard fails.
3. Attempts to restart the system automatically to preserve trading capabilities.
4. Will NEVER automatically modify code files unless given a PIN inside the terminal.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Fix relative imports
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from util.sms_client import send_sms

CHARTER_PIN = "841921"
LOG_FILE = ROOT / "logs" / "oanda_headless.log"
CHECK_INTERVAL_SECONDS = 30

def check_engine_crashed() -> bool:
    """Check if the headless supervisor or engine is dead"""
    try:
        sup = subprocess.run(["pgrep", "-f", "headless_runtime.py"], capture_output=True).stdout.strip()
        eng = subprocess.run(["pgrep", "-f", "oanda_trading_engine.py"], capture_output=True).stdout.strip()
        if not sup and not eng:
            return True
    except Exception:
        pass
    return False

def check_recent_errors() -> bool:
    """Scan the tail of the log for fatal Python tracing or specific error keywords."""
    if not LOG_FILE.exists():
        return False
    try:
        tail = subprocess.run(["tail", "-n", "100", str(LOG_FILE)], capture_output=True, text=True).stdout
        if "Traceback (most recent call last):" in tail or "FATAL ERROR" in tail:
            return True
    except Exception:
        pass
    return False

def restart_system():
    """Attempt a non-intrusive headless restart of the orchestrator to preserve trading."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Attempting automated system restart...")
    turn_on_script = ROOT / "turn_on.sh"
    if turn_on_script.exists():
        subprocess.run(["bash", str(turn_on_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Fallback to python execution
        subprocess.Popen([sys.executable, str(ROOT / "headless_runtime.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print("🛡️  Background Maintenance Agent Started.")
    print("Monitoring system health every 30 seconds.")
    
    last_crash_time = 0
    
    while True:
        try:
            time.sleep(CHECK_INTERVAL_SECONDS)
            
            crashed = check_engine_crashed()
            fatal_errors = check_recent_errors()
            
            if (crashed or fatal_errors) and (time.time() - last_crash_time > 300):
                last_crash_time = time.time()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚨 HARD FAIL DETECTED.")
                
                # 1. Send SMS Notification
                send_sms("🚨 RBOTZILLA HARD FAIL DETECTED. The engine crashed or generated fatal logs. Maintenance Agent is attempting an auto-restart.")
                
                # 2. Automatically repair runtime (reboot) without disrupting files
                restart_system()
                
                # Note: This agent runs as a daemon. It cannot interactively prompt for a PIN here
                # to "change code" because it has no tty. Code changes must be done via git by the developer.
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Restart command issued. Code changes require PIN {CHARTER_PIN} authorization manually.")

        except Exception as e:
            # Self healing
            try:
                send_sms(f"Maintenance Agent generated an internal exception: {e}")
            except:
                pass

if __name__ == "__main__":
    main()
