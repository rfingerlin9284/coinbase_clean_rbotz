#!/usr/bin/env python3
"""Headless runtime supervisor for PAPER/LIVE/BACKTEST.

Starts OANDA and Coinbase as fully independent child processes so one broker
failure does not stop the other.
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

from util.mode_manager import get_mode_info

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _oanda_cmd(mode: str) -> List[str]:
    env = "live" if mode == "LIVE" else "practice"
    cmd = [sys.executable, "oanda_trading_engine.py", "--env", env]
    if env == "live":
        cmd.append("--yes-live")
    return cmd


def _coinbase_cmd(mode: str) -> List[str]:
    env = "live" if mode == "LIVE" else "sandbox"
    return [sys.executable, "scripts/coinbase_headless.py", "--env", env]


def _spawn(name: str, command: List[str]) -> subprocess.Popen:
    log_path = LOG_DIR / f"{name}_headless.log"
    log_file = log_path.open("a", encoding="utf-8")
    return subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless broker runtime supervisor")
    parser.add_argument("--broker", choices=["oanda", "coinbase", "all"], default="all")
    args = parser.parse_args()

    info = get_mode_info()
    mode = info["mode"]

    if mode == "BACKTEST":
        print("BACKTEST mode active: live broker daemons are disabled.")
        print("Run backtesting manually from backtest scripts only.")
        return 0

    selected = {"oanda", "coinbase"} if args.broker == "all" else {args.broker}

    processes: Dict[str, subprocess.Popen] = {}
    if "oanda" in selected and info["brokers"].get("oanda", {}).get("enabled", False):
        processes["oanda"] = _spawn("oanda", _oanda_cmd(mode))
    if "coinbase" in selected and info["brokers"].get("coinbase", {}).get("enabled", False):
        processes["coinbase"] = _spawn("coinbase", _coinbase_cmd(mode))

    if not processes:
        print("No broker process started. Enable brokers via util.mode_manager.set_broker_enabled().")
        return 1

    print(f"Headless supervisor active in {mode} mode for: {', '.join(processes.keys())}")

    stop = False

    def _handle_stop(_sig, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    try:
        while not stop:
            for name, proc in list(processes.items()):
                code = proc.poll()
                if code is not None:
                    print(f"{name} exited with code {code}; other brokers remain unaffected.")
                    processes.pop(name)
            if not processes:
                print("All broker processes stopped.")
                return 1
            time.sleep(2)
    finally:
        for proc in processes.values():
            if proc.poll() is None:
                proc.terminate()
        for proc in processes.values():
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
