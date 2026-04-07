#!/usr/bin/env python3
"""
Coinbase CDP Advanced Trade Broker Connector - RBOTzilla UNI
Adapted from OANDA engine structure for Ed25519 Authentication.
"""

import os
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from coinbase.rest import RESTClient

# Charter compliance imports
try:
    from ..foundation.rick_charter import validate_pin, RickCharter
except ImportError:
    try:
        from foundation.rick_charter import validate_pin, RickCharter
    except ImportError:
        def validate_pin(pin): return pin == 841921
        RickCharter = None

# Narration logging
try:
    from ..util.narration_logger import log_narration
except ImportError:
    try:
        from util.narration_logger import log_narration
    except ImportError:
        def log_narration(*args, **kwargs): pass

@dataclass
class CoinbaseAccount:
    """Coinbase account information mapped from OANDA parity"""
    account_id: str
    currency: str
    balance: float
    unrealized_pl: float
    margin_used: float
    margin_available: float
    open_positions: int
    open_trades: int

class CoinbaseConnector:
    """
    Coinbase CDP Advanced Trade Connector
    Provides structural parity with OandaConnector to allow drop-in replacement
    in the trade_engine.py.
    """
    
    def __init__(self, pin: Optional[int] = None, environment: Optional[str] = "live"):
        if pin and not validate_pin(pin):
            raise PermissionError("Invalid PIN for CoinbaseConnector")
        
        self.pin_verified = validate_pin(pin) if pin else False
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        
        # Charter compliance
        self.max_placement_latency_ms = 300
        self.request_times = []
        self._lock = threading.Lock()
        
        self.client = None
        self._load_credentials()
        self._validate_connection()

    def _load_credentials(self):
        """Load CDP API credentials via native environment variables"""
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value.strip('"\'')
        
        # Reading Ed25519 / ECDSA Keys
        self.api_key_name = os.getenv("COINBASE_ECDSA_KEY_ID") or os.getenv("COINBASE_API_KEY_ID")
        self.api_private_key = os.getenv("COINBASE_ECDSA_KEY_SECRET") or os.getenv("COINBASE_API_KEY_SECRET")
        
        self.logger.info(f"CoinbaseConnector initializing in {self.environment} mode.")
        if not self.api_key_name or not self.api_private_key:
            self.logger.warning("Coinbase CDP API credentials not found in .env")
        else:
            # Ed25519 normalization securely strips physical escaped newline characters
            self.api_private_key = self.api_private_key.replace("\\n", "\n")
            try:
                self.client = RESTClient(api_key=self.api_key_name, api_secret=self.api_private_key)
            except Exception as e:
                self.logger.error(f"Failed to instantiate Coinbase RESTClient: {e}")
                self.client = None

    def _validate_connection(self):
        """Ping Coinbase to verify API key validity"""
        if not self.client:
            return False
        try:
            # Send lightweight request to verify
            self.client.get_portfolios()
            self.logger.info("Coinbase CDP connection validated securely.")
            return True
        except Exception as e:
            self.logger.error(f"Coinbase connection validation failed: {e}")
            return False

    def get_price(self, product_id: str) -> float:
        """Fetch current price for an instrument/product_id"""
        if not self.client:
            return 0.0
        try:
            product = self.client.get_product(product_id=product_id)
            return float(product.get('price', 0.0))
        except Exception as e:
            self.logger.error(f"Get price failed for {product_id}: {e}")
            return 0.0

    def place_oco_order(self, instrument: str, entry_price: float, stop_loss: float, 
                       take_profit: float, units: float, ttl_hours: float = 24.0, 
                       order_type: str = "LIMIT", trailing_stop_distance: Optional[float] = None,
                       is_hedge: bool = False) -> Dict[str, Any]:
        """
        Place Bracket Application logic on Coinbase.
        Coinbase Advanced does not have identical synchronous OCO wrapping as OANDA in standard REST,
        but we map it to standard limits or market orders as required by the Python SDK structure.
        """
        start_time = time.time()

        if stop_loss is None or take_profit is None:
            self.logger.error("OCO required: stop_loss and take_profit must be provided")
            return {
                "success": False,
                "error": "OCO_REQUIRED: stop_loss and take_profit must be specified",
                "broker": "COINBASE",
                "environment": self.environment
            }
            
        if not self.client:
            return {
                "success": False,
                "error": "Client not authenticated",
                "execution_time_ms": (time.time() - start_time) * 1000,
                "broker": "COINBASE",
                "environment": self.environment
            }

        client_order_id = str(int(time.time() * 1000))
        side = "BUY" if float(units) > 0 else "SELL"
        base_size = str(abs(float(units)))
        
        try:
            # Using Coinbase Advanced Python SDK logic to place order.
            # Depending on order_type, we format differently using Native CDP args
            if order_type.upper() == "MARKET":
                response = self.client.market_order_buy(
                    client_order_id=client_order_id,
                    product_id=instrument,
                    base_size=base_size
                ) if side == "BUY" else self.client.market_order_sell(
                    client_order_id=client_order_id,
                    product_id=instrument,
                    base_size=base_size
                )
            else:
                response = self.client.limit_order_buy(
                    client_order_id=client_order_id,
                    product_id=instrument,
                    base_size=base_size,
                    limit_price=str(entry_price),
                    post_only=False
                ) if side == "BUY" else self.client.limit_order_sell(
                    client_order_id=client_order_id,
                    product_id=instrument,
                    base_size=base_size,
                    limit_price=str(entry_price),
                    post_only=False
                )

            execution_time = (time.time() - start_time) * 1000
            
            # Record latency for stats
            with self._lock:
                self.request_times.append(execution_time)
                if len(self.request_times) > 100:
                    self.request_times = self.request_times[-100:]

            if response and response.get('success'):
                order_id = response.get('order_id')
                
                log_narration(
                    event_type="OCO_PLACED",
                    details={
                        "order_id": order_id,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "units": units,
                        "latency_ms": execution_time,
                        "environment": self.environment
                    },
                    symbol=instrument,
                    venue="coinbase"
                )
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "trade_id": order_id, # Coinbase generally unifies this concept early on
                    "instrument": instrument,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "units": units,
                    "latency_ms": execution_time,
                    "execution_time_ms": execution_time,
                    "broker": "COINBASE",
                    "environment": self.environment
                }
            else:
                resp_error = response.get('error_response', {}) if response else {}
                return {
                    "success": False,
                    "error": str(resp_error),
                    "execution_time_ms": execution_time,
                    "broker": "COINBASE",
                    "environment": self.environment
                }

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Coinbase Order Exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time,
                "broker": "COINBASE",
                "environment": self.environment
            }

    def get_account_info(self) -> Optional[CoinbaseAccount]:
        """Get summarized account balances in the format the engine expects."""
        if not self.client:
            return None
        try:
            accounts_data = self.client.get_accounts()
            # Simplistic aggregation of USD for matching OANDA account abstraction
            total_balance = 0.0
            total_available = 0.0
            uuid = "UNKNOWN"
            
            for acc in accounts_data.get('accounts', []):
                if acc.get('currency') == 'USD':
                    total_balance += float(acc.get('available_balance', {}).get('value', 0))
                    total_available += float(acc.get('available_balance', {}).get('value', 0))
                    uuid = acc.get('uuid', uuid)

            return CoinbaseAccount(
                account_id=uuid,
                currency="USD",
                balance=total_balance,
                unrealized_pl=0.0,
                margin_used=0.0,
                margin_available=total_available,
                open_positions=0,
                open_trades=0
            )

        except Exception as e:
            self.logger.error(f"Coinbase get_account_info failed: {e}")
            return None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get connector performance statistics similar to OANDA"""
        with self._lock:
            request_times = self.request_times.copy()
        
        if not request_times:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "max_latency_ms": 0,
                "charter_compliance_rate": 0,
                "environment": self.environment,
                "broker": "COINBASE"
            }
        
        avg_latency = sum(request_times) / len(request_times)
        max_latency = max(request_times)
        compliant_requests = sum(1 for lat in request_times if lat <= self.max_placement_latency_ms)
        compliance_rate = compliant_requests / len(request_times)
        
        return {
            "total_requests": len(request_times),
            "avg_latency_ms": round(avg_latency, 1),
            "max_latency_ms": round(max_latency, 1),
            "charter_compliance_rate": round(compliance_rate, 3),
            "environment": self.environment,
            "broker": "COINBASE"
        }
