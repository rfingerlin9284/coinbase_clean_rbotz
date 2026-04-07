#!/usr/bin/env python3
"""
Master Orchestrator Shell — RBOTzilla Phoenix (Phase 4)
-------------------------------------------------------
Acts as the 'Brain', uniting the OANDA Forex Engine and the
Coinbase Crypto Connector into a single continuous intelligence loop.
Maintains the heartbeat of both systems and pauses Forex on weekends
while keeping Crypto (24/7) alive.
"""

import sys
import time
import asyncio
from datetime import datetime

try:
    from brokers.coinbase_connector import CoinbaseConnector
    from oanda_trading_engine import OandaTradingEngine
    from util.terminal_display import TerminalDisplay
except ImportError as e:
    print(f"❌ Failed to import core modules: {e}")
    sys.exit(1)

import argparse

class BrokerRouter:
    def __init__(self, oanda_env='practice'):
        self.display = TerminalDisplay()
        self.display.alert("Initializing Master Broker Router...", "INFO")
        
        # Initialize the connectors
        try:
            self.coinbase = CoinbaseConnector(environment='live')
            self.display.success("✅ Coinbase Crypto Engine Linked (LIVE)")
        except Exception as e:
            self.display.error(f"❌ Coinbase Initialization Failed: {e}")
            self.coinbase = None

        try:
            self.oanda_engine = OandaTradingEngine(environment=oanda_env)
            self.display.success(f"✅ OANDA Forex Engine Linked ({oanda_env.upper()} mode)")
        except Exception as e:
            self.display.error(f"❌ OANDA Initialization Failed: {e}")
            self.oanda_engine = None

    def is_forex_weekend(self) -> bool:
        """
        Forex markets close Friday 5 PM EST to Sunday 5 PM EST.
        Using simple UTC bounds for weekend logic.
        Friday 21:00 UTC -> Sunday 21:00 UTC (approx. depending on DST)
        """
        now = datetime.utcnow()
        if now.weekday() == 5: # Saturday
            return True
        if now.weekday() == 6 and now.hour < 21: # Sunday before 5 PM EST
            return True
        if now.weekday() == 4 and now.hour >= 21: # Friday after 5 PM EST
            return True
        return False

    async def _cryptocurrency_heartbeat(self):
        """Pulls a single price to confirm the pipeline is active."""
        if not self.coinbase:
            return
            
        try:
            # Hit the products endpoint directly through _make_request
            result = self.coinbase._make_request("GET", "/api/v3/brokerage/products/BTC-USD")
            if "price" in result:
                price_str = result.get("price")
                self.display.info(f"🪙  COINBASE HEARTBEAT: BTC-USD @ ${float(price_str):,.2f}", "", "\033[96m")
            else:
                self.display.info("🪙  COINBASE HEARTBEAT: Ping successful (Pipeline Online)", "", "\033[96m")
        except Exception as e:
            self.display.warning(f"⚠️  Coinbase Heartbeat failed: {e}")

    async def run_master_loop(self):
        """Unified Master Loop"""
        self.display.alert("===================================================", "INFO")
        self.display.alert("  🤖 Starting Universal Signal Routing System 🤖 ", "SUCCESS")
        self.display.alert("===================================================", "INFO")
        
        oanda_task = None
        
        if not self.oanda_engine:
            self.display.error("Cannot start OANDA Engine - missing initial connection.")
        elif not self.is_forex_weekend():
            self.display.info("Forex markets open. Booting OANDA subsystem...", "")
            oanda_task = asyncio.create_task(self.oanda_engine.run_trading_loop())
        else:
            self.display.warning("Forex markets closed (Weekend). OANDA Engine paused.")
            
        self.display.info("Crypto markets open (24/7). Activating Coinbase pipeline...", "")
        
        try:
            while True:
                # -------------------------------------------------------------
                # 1. Dispatch Check
                # -------------------------------------------------------------
                currently_weekend = self.is_forex_weekend()
                
                # Check if we need to pause OANDA for the weekend
                if currently_weekend and oanda_task and not oanda_task.done():
                    self.display.warning("Market Close Detected: Pausing OANDA pipeline for weekend...")
                    oanda_task.cancel()
                    oanda_task = None
                
                # Check if we need to resume OANDA after the weekend
                elif not currently_weekend and not oanda_task and self.oanda_engine:
                    self.display.success("Market Open Detected: Resuming OANDA pipeline...")
                    oanda_task = asyncio.create_task(self.oanda_engine.run_trading_loop())
                
                # -------------------------------------------------------------
                # 2. Pipeline Logs
                # -------------------------------------------------------------
                await self._cryptocurrency_heartbeat()
                
                # Sleep between heartbeats/scans
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            if oanda_task:
                oanda_task.cancel()
            self.display.alert("Master Orchestrator Shutting Down", "WARNING")
            
        except KeyboardInterrupt:
            # Handle standard termination
            if oanda_task:
                oanda_task.cancel()
            self.display.alert("Master Orchestrator Shutting Down", "WARNING")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Orchestrator Shell")
    parser.add_argument("--env", type=str, default="practice", choices=["live", "practice"], help="OANDA API Environment")
    parser.add_argument("--yes-live", action="store_true", help="Confirm real money API")
    args = parser.parse_args()

    router = BrokerRouter(oanda_env=args.env)
    
    # Run the main asyncio event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(router.run_master_loop())
    except KeyboardInterrupt:
        print("\n⏹️  Master Router halted by user.")
        
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop=loop)
    for task in pending:
        task.cancel()
    
    # Stop the loop
    if loop.is_running():
        loop.stop()
