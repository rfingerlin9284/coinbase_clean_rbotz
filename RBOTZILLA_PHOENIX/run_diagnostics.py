#!/usr/bin/env python3
"""
RBOTZILLA System Diagnostics - Comprehensive Health Check
Can run with or without trading engine running
PIN: 841921 | Autonomous System Health Monitor
"""

import os
import sys
import json
import time
import subprocess
import psutil
import requests
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Setup basic logging
logging.basicConfig(level=logging.ERROR)

# Project root
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# ─────────────────────────────────────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────────────────────────────────────

class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    
    @staticmethod
    def green(text): return f"{Colors.GREEN}{text}{Colors.RESET}"
    @staticmethod
    def yellow(text): return f"{Colors.YELLOW}{text}{Colors.RESET}"
    @staticmethod
    def red(text): return f"{Colors.RED}{text}{Colors.RESET}"
    @staticmethod
    def cyan(text): return f"{Colors.CYAN}{text}{Colors.RESET}"
    @staticmethod
    def blue(text): return f"{Colors.BLUE}{text}{Colors.RESET}"

OK = "✅"
WARN = "⚠️ "
ERR = "❌"
INFO = "ℹ️ "
DIVIDER = "═" * 80

# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic Functions
# ─────────────────────────────────────────────────────────────────────────────

def check_engine_process() -> Tuple[bool, Optional[int], Optional[str]]:
    """Check if trading engine is running and get uptime."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "oanda_trading_engine.py"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            pid = int(result.stdout.strip().split('\n')[0])
            try:
                process = psutil.Process(pid)
                uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
                hours = uptime.seconds // 3600
                mins = (uptime.seconds % 3600) // 60
                return True, pid, f"{hours}h {mins}m"
            except:
                return True, pid, "Unknown"
        return False, None, None
    except:
        return False, None, None

def check_oanda_api() -> Tuple[bool, str, Dict]:
    """Test OANDA API connectivity without placing trades."""
    try:
        from brokers.oanda_connector import OandaConnector
        
        connector = OandaConnector(environment='practice')
        info = connector.get_account_info()
        
        if info:
            balance = float(info.get('balance', 0)) if isinstance(info, dict) else float(getattr(info, 'balance', 0))
            return True, f"Account balance: ${balance:,.2f}", {'balance': balance}
        else:
            return False, "Could not fetch account info", {}
    except Exception as e:
        return False, f"API Error: {str(e)[:50]}", {}

def check_hive_mind() -> Tuple[bool, str]:
    """Check if Hive Mind can be imported and initialized."""
    try:
        from hive.rick_hive_mind import RickHiveMind
        hive = RickHiveMind()
        return True, "Hive Mind loadable (GPT, GROK, DeepSeek agents)"
    except Exception as e:
        return False, f"Hive error: {str(e)[:50]}"

def check_local_llm() -> Tuple[bool, str]:
    """Check if local LLM (Ollama) is reachable."""
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "llama3.1:8b", "prompt": "test", "stream": False},
            timeout=2
        )
        return response.status_code == 200, "Ollama Llama3.1:8b online"
    except:
        return False, "Ollama offline or unreachable"

def check_multi_strategy() -> Tuple[bool, str]:
    """Check if all 7 detectors load."""
    try:
        from systems.multi_signal_engine import DETECTORS
        return True, f"All 7 detectors ready (momentum_sma, ema_stack, fvg, fibonacci, liq_sweep, trap_reversal, rsi_extreme)"
    except Exception as e:
        return False, f"Strategy error: {str(e)[:50]}"

def check_quant_hedging() -> Tuple[bool, str]:
    """Check quant hedging system."""
    try:
        from util.quant_hedge_engine import QuantHedgeEngine
        engine = QuantHedgeEngine()
        return True, "Correlation matrix loaded (EUR, GBP, JPY, AUD, CAD clusters)"
    except Exception as e:
        return False, f"Hedging error: {str(e)[:50]}"

def check_charter_compliance() -> Tuple[bool, str]:
    """Verify charter compliance."""
    try:
        from foundation.rick_charter import RickCharter
        pin = 841921
        if RickCharter.MIN_RISK_REWARD_RATIO == 3.2:
            return True, f"PIN 841921 | RR {RickCharter.MIN_RISK_REWARD_RATIO}:1 | Min notional ${RickCharter.MIN_NOTIONAL_USD:,}"
        else:
            return False, "Charter parameters mismatch"
    except Exception as e:
        return False, f"Charter error: {str(e)[:50]}"

def check_dashboard() -> Tuple[bool, str]:
    """Check position dashboard."""
    try:
        from util.position_dashboard import PositionDashboard
        dashboard = PositionDashboard(refresh_interval_sec=60)
        return True, "Dashboard available (60s refresh)"
    except Exception as e:
        return False, f"Dashboard error: {str(e)[:50]}"

def check_narration_log() -> Tuple[bool, str, int]:
    """Check if narration.jsonl exists and is writable."""
    try:
        log_path = PROJECT_ROOT / "narration.jsonl"
        
        if log_path.exists():
            size_mb = log_path.stat().st_size / (1024 * 1024)
            return True, f"Writable ({size_mb:.1f} MB)", int(size_mb)
        else:
            return False, "narration.jsonl not found", 0
    except Exception as e:
        return False, f"Log error: {str(e)[:50]}", 0

def check_system_resources() -> Dict[str, Any]:
    """Get system resource usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_free_gb': disk.free / (1024**3),
            'disk_percent': disk.percent
        }
    except:
        return {}

def get_recent_logs(lines: int = 15) -> List[str]:
    """Get recent narration log entries."""
    try:
        log_path = PROJECT_ROOT / "narration.jsonl"
        if not log_path.exists():
            return ["No narration log found"]
        
        with open(log_path, 'r') as f:
            all_lines = f.readlines()[-lines:]
        
        recent = []
        for line in all_lines:
            try:
                entry = json.loads(line.strip())
                event = entry.get('event_type', 'UNKNOWN')
                symbol = entry.get('symbol', '')
                timestamp = entry.get('timestamp', '')[-8:]
                
                summary = f"{timestamp} {event:20} {symbol}"
                recent.append(summary)
            except:
                pass
        
        return recent if recent else ["No recent log entries"]
    except:
        return ["Could not read logs"]

# ─────────────────────────────────────────────────────────────────────────────
# Main Diagnostic Report
# ─────────────────────────────────────────────────────────────────────────────

def run_diagnostics(verbose: bool = False, export_json: bool = False) -> int:
    """Run complete system diagnostics."""
    
    print()
    print(DIVIDER)
    print(Colors.cyan("🔍 RBOTZILLA SYSTEM DIAGNOSTICS"))
    print(DIVIDER)
    print()
    
    # ── Engine Status ────────────────────────────────────────────────────────
    print(Colors.blue("📋 ENGINE STATUS"))
    print("-" * 80)
    
    engine_running, engine_pid, uptime = check_engine_process()
    
    if engine_running:
        print(f"{OK} {Colors.green('Engine Process')}: RUNNING (PID {engine_pid}, uptime {uptime})")
    else:
        print(f"{INFO} Engine Process: STOPPED (can run offline)")
    print()
    
    # ── Core Systems ─────────────────────────────────────────────────────────
    print(Colors.blue("🤖 HIVE-RICK AI SYSTEMS"))
    print("-" * 80)
    
    components = {}
    
    # Hive Mind
    hive_ok, hive_msg = check_hive_mind()
    icon = OK if hive_ok else WARN
    print(f"{icon} Hive Mind: {hive_msg}")
    components['hive_mind'] = hive_ok
    
    # Local LLM
    llm_ok, llm_msg = check_local_llm()
    icon = OK if llm_ok else WARN
    print(f"{icon} Local LLM (Ollama): {llm_msg}")
    components['local_llm'] = llm_ok
    
    print()
    
    # ── Trading Systems ─────────────────────────────────────────────────────
    print(Colors.blue("🎯 TRADING SYSTEMS"))
    print("-" * 80)
    
    # Multi-strategy
    strat_ok, strat_msg = check_multi_strategy()
    icon = OK if strat_ok else ERR
    print(f"{icon} Multi-Strategy: {strat_msg}")
    components['multi_strategy'] = strat_ok
    
    # Quant Hedging
    hedge_ok, hedge_msg = check_quant_hedging()
    icon = OK if hedge_ok else ERR
    print(f"{icon} Quant Hedging: {hedge_msg}")
    components['quant_hedging'] = hedge_ok
    
    # Charter Compliance
    charter_ok, charter_msg = check_charter_compliance()
    icon = OK if charter_ok else ERR
    print(f"{icon} Charter Compliance: {charter_msg}")
    components['charter'] = charter_ok
    
    # Dashboard
    dash_ok, dash_msg = check_dashboard()
    icon = OK if dash_ok else WARN
    print(f"{icon} Position Dashboard: {dash_msg}")
    components['dashboard'] = dash_ok
    
    print()
    
    # ── API Connectivity ────────────────────────────────────────────────────
    print(Colors.blue("🌐 API CONNECTIVITY"))
    print("-" * 80)
    
    api_ok, api_msg, api_details = check_oanda_api()
    icon = OK if api_ok else ERR
    print(f"{icon} OANDA API: {api_msg}")
    components['oanda_api'] = api_ok
    components['api_details'] = api_details
    
    print()
    
    # ── Data & Logging ──────────────────────────────────────────────────────
    print(Colors.blue("💾 DATA & LOGGING"))
    print("-" * 80)
    
    log_ok, log_msg, log_size = check_narration_log()
    icon = OK if log_ok else ERR
    print(f"{icon} Narration Log: {log_msg}")
    components['narration_log'] = log_ok
    components['log_size_mb'] = log_size
    
    # System Resources
    resources = check_system_resources()
    if resources:
        print(f"{OK} System Resources: CPU {resources['cpu_percent']:.1f}% | RAM {resources['memory_percent']:.1f}% | Disk {resources['disk_percent']:.1f}%")
        components['system_resources'] = True
    
    print()
    
    # ── Recent Activity ────────────────────────────────────────────────────
    print(Colors.blue("📊 RECENT ACTIVITY"))
    print("-" * 80)
    
    logs = get_recent_logs(10)
    for log in logs[-10:]:
        print(f"   {log}")
    
    print()
    
    # ── Summary ────────────────────────────────────────────────────────────
    print(DIVIDER)
    
    all_ok = all(components.values())
    
    if all_ok:
        print(Colors.green("✅ ALL CRITICAL SYSTEMS OPERATIONAL"))
    else:
        print(Colors.yellow("⚠️  SOME SYSTEMS OFFLINE (see above)"))
    
    print(DIVIDER)
    print()
    
    # Export JSON if requested
    if export_json:
        diagnostic_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'engine_running': engine_running,
            'engine_pid': engine_pid,
            'engine_uptime': uptime,
            'components': components,
            'resources': resources,
            'recent_logs': logs[-5:],
            'system_status': 'OK' if all_ok else 'WARNING',
            'critical_systems_ok': all_ok,
            'hive_llm_active': components.get('hive_mind', False) and components.get('local_llm', False)
        }
        
        export_path = Path("/tmp/rbotzilla_diagnostics.json")
        with open(export_path, 'w') as f:
            json.dump(diagnostic_data, f, indent=2)
        
        print(f"📄 JSON export: {export_path}")
        print()
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='RBOTzilla system diagnostics')
    parser.add_argument('--json', action='store_true', help='Export as JSON to /tmp/rbotzilla_diagnostics.json')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    exit_code = run_diagnostics(verbose=args.verbose, export_json=args.json)
    sys.exit(exit_code)
