#!/usr/bin/env python3
"""
Coinbase CDP Advanced Trade Broker Connector - RBOTzilla UNI
Structurally mapped to emulate OANDA Engine signatures, enabling
seamless drop-in replacement for the OANDA Trade Engine.
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from coinbase.rest import RESTClient

try:
    from foundation.rick_charter import validate_pin, RickCharter
except ImportError:
    try:
        from ..foundation.rick_charter import validate_pin, RickCharter
    except ImportError:
        def validate_pin(pin): return pin == 841921
        RickCharter = None

try:
    from util.narration_logger import log_narration
except ImportError:
    try:
        from ..util.narration_logger import log_narration
    except ImportError:
        def log_narration(*args, **kwargs): pass

@dataclass
class CoinbaseAccount:
    account_id: str
    currency: str
    balance: float
    unrealized_pl: float
    margin_used: float
    margin_available: float
    open_positions: int
    open_trades: int

class CoinbaseConnector:
    def __init__(self, pin: Optional[int] = None, environment: Optional[str] = "live"):
        if pin and not validate_pin(pin):
            raise PermissionError("Invalid PIN for CoinbaseConnector")
        
        self.pin_verified = validate_pin(pin) if pin else False
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        self.max_placement_latency_ms = 300
        self._lock = threading.Lock()
        self.client = None
        self.client = None
        self.account_uuid = ""
        self.active_trades_path = os.path.join("logs", "active_coinbase_trades.json")
        self.active_trades = self._load_active_trades()
        self._load_credentials()

    def _load_active_trades(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.active_trades_path):
                import json
                with open(self.active_trades_path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_active_trades(self):
        try:
            import json
            with open(self.active_trades_path, "w") as f:
                json.dump(self.active_trades, f)
        except Exception:
            pass

    def _load_credentials(self):
        """Load CDP ECDSA credentials from .env using standardized variable names.
        
        Expected .env variables:
            COINBASE_API_KEY    = "organizations/{org_id}/apiKeys/{key_id}"
            COINBASE_API_SECRET = "-----BEGIN EC PRIVATE KEY-----\\n...\\n-----END EC PRIVATE KEY-----"
        """
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip('"\'')
        
        # Canonical variable names matching official SDK convention
        self.api_key_name = os.getenv("COINBASE_API_KEY")
        self.api_private_key = os.getenv("COINBASE_API_SECRET")
        
        self.logger.info(f"CoinbaseConnector initializing in {self.environment} mode.")
        
        if not self.api_key_name or not self.api_private_key:
            self.logger.error(
                "COINBASE_API_KEY and/or COINBASE_API_SECRET not found in .env. "
                "Generate a CDP ECDSA key at https://portal.cdp.coinbase.com/projects/api-keys"
            )
            return
        
        # Unescape PEM newlines: .env stores literal \n but PEM needs real newlines
        self.api_private_key = self.api_private_key.replace("\\n", "\n")
        
        try:
            self.client = RESTClient(api_key=self.api_key_name, api_secret=self.api_private_key)
            # Quick validation: attempt to list accounts to confirm the key works
            test = self.client.get_accounts(limit=1)
            acct_list = test.accounts if hasattr(test, "accounts") else test.get('accounts', [])
            self.logger.info(f"✅ CDP ECDSA Auth SUCCESS — {len(acct_list)} account(s) visible")
        except Exception as e:
            self.client = None
            self.logger.error(f"❌ CDP Auth FAILED: {e}")

    @property
    def api_base(self):
        return "https://api.coinbase.com/api/v3/brokerage"

    @property
    def account_id(self):
        return self.account_uuid or "Coinbase-Spot-Master"

    def get_account_info(self) -> CoinbaseAccount:
        if not self.client:
            return CoinbaseAccount("", "USD", 0.0, 0.0, 0.0, 0.0, 0, 0)
        try:
            # Aggregate USD value of total spot portfolio as balance (Includes Crypto + Fiat)
            acct = self.client.get_accounts()
            total_usd = 0.0
            acc_list = acct.accounts if hasattr(acct, "accounts") else acct.get('accounts', [])
            for a in acc_list:
                curr = getattr(a, "currency", a.get("currency")) if hasattr(a, "get") else a.currency
                avail = getattr(a, "available_balance", a.get("available_balance", {})) if hasattr(a, "get") else getattr(a, "available_balance", None)
                v = float(getattr(avail, "value", avail.get("value", 0.0)) if hasattr(avail, "get") else (avail.value if avail else 0.0))
                
                if v > 0.0001:
                    if curr in ['USDC', 'USD']:
                        total_usd += v
                    else:
                        # Convert crypto balances to USD to factor into total NAV
                        try:
                            px = self.get_price(f"{curr}-USD")
                            if px:
                                total_usd += (v * float(px))
                        except Exception:
                            pass
                            
            return CoinbaseAccount(self.account_id, "USD", float(total_usd), 0.0, 0.0, float(total_usd), 0, 0)
        except Exception as e:
            self.logger.error(f"Failed to fetch account info: {e}")
            return CoinbaseAccount("", "USD", 0.0, 0.0, 0.0, 0.0, 0, 0)

    def get_trades(self) -> List[Dict]:
        """Returns active open OCO brackets mapping to trades for the engine."""
        return list(self.active_trades.values())

    def get_price(self, product_id: str) -> float:
        if not self.client: return 0.0
        try:
            product = self.client.get_product(product_id=product_id)
            px = getattr(product, 'price', product.get('price', 0.0)) if hasattr(product, 'get') else product.price
            return float(px)
        except Exception:
            return 0.0

    def get_live_prices(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        res = {}
        for s in symbols:
            px = self.get_price(s)
            if px:
                res[s] = {"mid": px}
        return res

    def get_usd_notional(self, units: float, symbol: str, price: float) -> float:
        return abs(float(units) * price)

    def get_historical_data(self, instrument: str, count: int = 500, granularity: str = "H1") -> List[Dict]:
        # Translates OANDA-style granularities to Coinbase granularity strings
        gran_map = {
            "M1": "ONE_MINUTE",
            "M5": "FIVE_MINUTE",
            "M15": "FIFTEEN_MINUTE",
            "M30": "THIRTY_MINUTE",
            "H1": "ONE_HOUR",
            "H2": "TWO_HOUR",
            "H4": "FOUR_HOUR",
            "H6": "SIX_HOUR",
            "D": "ONE_DAY"
        }
        cb_gran = gran_map.get(granularity, "FIFTEEN_MINUTE")
        
        # Calculate start/end time approx based on count
        sec_per_cand = 900
        if cb_gran == "ONE_MINUTE": sec_per_cand = 60
        elif cb_gran == "FIVE_MINUTE": sec_per_cand = 300
        elif cb_gran == "THIRTY_MINUTE": sec_per_cand = 1800
        elif cb_gran == "ONE_HOUR": sec_per_cand = 3600
        elif cb_gran == "TWO_HOUR": sec_per_cand = 7200
        elif cb_gran == "FOUR_HOUR": sec_per_cand = 14400
        elif cb_gran == "SIX_HOUR": sec_per_cand = 21600
        elif cb_gran == "ONE_DAY": sec_per_cand = 86400
        
        end_ts = int(time.time())
        start_ts = end_ts - (count * sec_per_cand)
        
        if not self.client: return []
        try:
            time.sleep(0.15) # Ratelimit buffer for rapid scans
            candles = self.client.get_public_candles(product_id=instrument, start=str(start_ts), end=str(end_ts), granularity=cb_gran)
            results = []
            cand_list = candles.candles if hasattr(candles, "candles") else candles.get('candles', [])
            for c in cand_list:
                b_time = getattr(c, 'start', c.get('start')) if hasattr(c, 'get') else c.start
                o = getattr(c, 'open', c.get('open', 0.0)) if hasattr(c, 'get') else c.open
                h = getattr(c, 'high', c.get('high', 0.0)) if hasattr(c, 'get') else c.high
                l = getattr(c, 'low', c.get('low', 0.0)) if hasattr(c, 'get') else c.low
                cls = getattr(c, 'close', c.get('close', 0.0)) if hasattr(c, 'get') else c.close
                v = getattr(c, 'volume', c.get('volume', 0.0)) if hasattr(c, 'get') else c.volume
                
                results.append({
                    "time": b_time,
                    "mid": {
                        "o": float(o),
                        "h": float(h),
                        "l": float(l),
                        "c": float(cls)
                    },
                    "volume": int(float(v))
                })
            # Coinbase returns newest first or oldest first depending on the epoch. Oanda engine expects oldest first.
            results.sort(key=lambda x: int(x['time']))
            return results
        except Exception as e:
            self.logger.error(f"Failed to fetch {instrument} candles: {e}")
            return []

    def place_oco_order(self, instrument: str, entry_price: float, stop_loss: float, 
                        take_profit: float, units: float, order_type: str = "MARKET", 
                        trailing_stop_distance: Optional[float] = None, is_hedge: bool=False) -> Dict[str, Any]:
        """
        Emulates full OCO bracket for spot trades by posting market order, 
        and then ideally posting OCO stop restrictions (not explicitly supported directly via single api config in the same way as forex, 
        so we wrap it as best as Coinbase allows via stop_limits or we emulate logic).
        """
        if not self.client: return {"success": False, "error": "No Client"}
        
        side = "BUY" if float(units) > 0 else "SELL"
        amount = abs(float(units))
        
        try:
            # We place the market order payload natively
            import uuid
            order_id = str(uuid.uuid4())
            res = self.client.create_order(
                client_order_id=order_id,
                product_id=instrument,
                side=side,
                order_configuration={
                    "market_market_ioc": {
                        "base_size": str(amount) if side == "SELL" else None,
                        "quote_size": str(round(amount * entry_price, 2)) if side == "BUY" else None
                    }
                }
            )
            is_success = getattr(res, 'success', False) if not isinstance(res, dict) else res.get('success', False)
            if is_success:
                succ_resp = getattr(res, 'success_response', None) if not isinstance(res, dict) else res.get('success_response', {})
                cb_order_id = getattr(succ_resp, 'order_id', order_id) if not isinstance(succ_resp, dict) else succ_resp.get('order_id', order_id)
                # To maintain OCO safety parity, we immediately log the brackets locally to TradeManager
                self.active_trades[cb_order_id] = {
                    "id": cb_order_id,
                    "instrument": instrument,
                    "currentUnits": units,
                    "price": float(entry_price),
                    "unrealizedPL": 0.0,
                    "stopLossOrder": {"price": float(stop_loss)},
                    "takeProfitOrder": {"price": float(take_profit)}
                }
                self._save_active_trades()
                
                return {
                    "success": True,
                    "trade_id": cb_order_id,
                    "confirmed": True,
                    "entry_price": float(entry_price),
                    "live_api": True
                }
            else:
                err_resp = getattr(res, 'error_response', None) if not isinstance(res, dict) else res.get('error_response')
                err_msg = getattr(err_resp, 'message', getattr(err_resp, 'error', str(res))) if err_resp else 'Unknown SDK Object payload'
                return {"success": False, "error": f"API REJECTION: {err_msg}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_trade(self, trade_id: str, units: Optional[float] = None) -> bool:
        """Emulates trade closure by sending native spot offset market order explicitly to sell held crypto. Supports partial scale-outs."""
        if not self.client: return False
        
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
            
        try:
            current_units = float(trade["currentUnits"])
            amount = abs(units) if units is not None else abs(current_units)
            side = "SELL" if current_units > 0 else "BUY"
            
            # If full close, pop it. If partial close, deduct units.
            if units is None or amount >= abs(current_units):
                self.active_trades.pop(trade_id, None)
            else:
                trade["currentUnits"] = current_units - (amount if current_units > 0 else -amount)
            self._save_active_trades()
            
            import uuid
            res = self.client.create_order(
                client_order_id=str(uuid.uuid4()),
                product_id=trade["instrument"],
                side=side,
                order_configuration={
                    "market_market_ioc": {
                        "base_size": str(amount) if side == "SELL" else None,
                        "quote_size": str(round(amount * trade["price"], 2)) if side == "BUY" else None
                    }
                }
            )
            return res.get('success', False)
        except Exception as e:
            self.logger.error(f"Error closing trade {trade_id}: {e}")
            return False

    def set_trade_stop(self, trade_id: str, new_sl: float) -> bool:
        """Local-only SL update for naked crypto execution.
        Coinbase spot has no broker-side SL orders — the trade_manager
        tracks and enforces stops internally via price monitoring."""
        trade = self.active_trades.get(str(trade_id))
        if trade:
            trade["stopLossOrder"] = {"price": str(new_sl)}
            self._save_active_trades()
        return True

def get_coinbase_connector(pin: Optional[int] = None) -> CoinbaseConnector:
    return CoinbaseConnector(environment="live")
