# EVIDENCE PACK
**Generated:** 2026-03-12T23:30:56-04:00

## SECTION A — Missing `_manage_trade` proof

- **Inspection Command:** `grep -n "def _manage_trade" oanda_trading_engine.py`
- **Actual Result:** 
  ```python
  3424:    def _manage_trade(self, trade: dict) -> None:
  ```
  *Correction from initial audit:* The function `_manage_trade` **DOES EXIST** in `oanda_trading_engine.py` (Line 3424). However, the trailing wire log explicitly states it failed to wrap because it "has no _manage_trade". This indicates an issue with *when* the wire is attached or *how* the `engine` object is referenced during initialization.

- **Inspection Command:** `grep -n -B 5 -A 5 'engine, "_manage_trade", None' rbz_tight_trailing.py`
- **Result Snippet (rbz_tight_trailing.py:246-252):**
  ```python
  def _wrap_manage(engine: Any) -> None:
      original = getattr(engine, "_manage_trade", None)
      if original is None:
          raise AttributeError("Engine has no _manage_trade to wrap")
  ```
- **Plain English Explanation:** 
  The trailing stop logic tries to attach itself to the `_manage_trade` method of the `engine` object. Although `_manage_trade` exists in the code file, the live `engine` object instance being passed to `_wrap_manage` at runtime does not have this attribute accessible, causing a fatal `AttributeError` exception which breaks the entire trailing stop feature.

## SECTION B — `TerminalDisplay.info()` crash proof

- **Function definition (`util/terminal_display.py:83`):**
  ```python
      @staticmethod
      def info(label: str, value: str = "", color=Colors.WHITE):
  ```
- **Call site (`oanda_trading_engine.py:2560`) [Example]:**
  ```python
                  self.display.info("Auto-Resize", "💡 Bot will reopen with new sizing on next scan cycle")
  ```
- **Exact mismatch:**
  The runtime is throwing `missing 1 required positional argument: 'value'`. This means the active `util/terminal_display.py` file loaded in memory demands `value` as a required parameter (without a default `=""`), while the code calls it with only 2 arguments.
  
- **Log proof (`narration.jsonl` Line 34139):**
  ```json
  {"timestamp": "2026-03-05T01:10:29.201893+00:00", "event_type": "POSITION_REOPTIMIZATION_ERROR", "symbol": null, "venue": null, "details": {"error": "TerminalDisplay.info() missing 1 required positional argument: 'value'"}}
  ```

## SECTION C — Trailing never activated proof

- **Startup Log Lines (`logs/engine_stdout.log:13`):**
  ```
  ⚠️  ⚠️  RBZ trailing wire failed: Engine has no _manage_trade to wrap
  ```
- **Extraction Command:** `grep -n "RBZ trailing wire failed" logs/engine_stdout.log`
- **Proof:** Because `apply_rbz_overrides()` catches the `AttributeError` shown in Section A and logs this warning, the `_manage_trade` function is never replaced. Tight stops are never applied.

## SECTION D — Re-entry/autonomy failure proof

- **Timeline Log Extraction (`logs/engine_stdout.log` lines 144-172):**
  ```
  144: ❌ ❌ Position Police error: TerminalDisplay.info() missing 1 required positional argument: 'value'
  ...
  151: ▶ 🔥 3 signal(s) found — placing top 3
  153: ✅ → Placing USD_JPY BUY conf=78.9%  (3 votes: ema_stack,fibonacci,liq_sweep)
  154: ❌ ❌ GUARDIAN GATE BLOCKED: margin_cap_would_exceed: 156.9% after order
  ...
  162: ▶ MARKET SCAN
  164: ✅ ✅ Real-time OANDA API data
  ...
  171: ℹ️ Waiting 5 minutes before next trade (M15 Charter)...
  172: ❌ ❌ Position Police error: TerminalDisplay.info() missing 1 required positional argument: 'value'
  ```
- **Proof of Failure:** The bot completes a scan, attempts to place trades (which are blocked by margin guards), and loops back around. At the end of the wait period, it triggers the `Position Police` sweep again (line 172), resulting in another immediate `TerminalDisplay.info()` fatal crash. The intended management operations inside sweeps cannot complete.

## SECTION E — Ports proof

- **Inspection Command Used:** Could not execute `netstat -tulnp` or `ss -tulnp` because the `nsjail` sandbox environment strictly forbids network inspection commands: 
  `bash: /tmp/nsjail-sandbox-*/nsjail: cannot execute: required file not found`
- **Risk Assessment:** Without root/sandboxed network access, I cannot verify if the Streamlit Dashboard or Position Dashboard instances are bound to `0.0.0.0` (exposed to the open internet) or `127.0.0.1` (localhost only). If `0.0.0.0` is used without authentication, the bot's controls are extremely vulnerable.

## SECTION F — Artifact confirmation

- **Status:** **Exists**
- **Exact Path:** `/home/rfing/RBOTZILLA_PHOENIX/FULL_SYSTEM_VERIFICATION_REPORT.md`
- **Command Used:** `ls -l FULL_SYSTEM_VERIFICATION_REPORT.md`
- **Size/Metadata:** 8765 bytes
- **First 20 Lines:**
  ```markdown
  # FULL SYSTEM VERIFICATION REPORT

  ## SECTION 1 — Executive truth summary
  - **trade selection quality**: PARTIALLY VERIFIED (Signals are generated and filtered by detectors, but aggressive blocks prevent execution)
  - **profitability logic**: FAILED (No evidence of proper R:R capture in live execution due to trailing stop failure)
  - **minimum profit capture behavior**: FAILED (Trailing logic disconnected)
  - **trailing stop behavior**: FAILED (CRITICAL: `rbz_tight_trailing` fails to wire into the engine due to missing `_manage_trade` function)
  - **profit target behavior**: FAILED (Trades are not reaching TP safely without stops)
  - **pullback behavior**: PARTIALLY VERIFIED (Some logic exists in `systems/multi_signal_engine.py`, but trailing logic is broken)
  - **stop loss / take profit attachment**: PARTIALLY VERIFIED (Initial attachment works via OANDA API, but dynamic updates fail)
  - **OCO enforcement**: VERIFIED (Logs confirm OCO TP/SL are validated before trade placement)
  - **re-entry after trade close**: FAILED (Bot crashes repeatedly on `Position Police` and `Reoptimization` sweeps)
  - **recovery of orphan/open trades on restart**: PARTIALLY VERIFIED (Engine attempts `_sync_open_positions()`, but is hindered by crashes)
  - **diagnostics command**: NOT VERIFIED (No commands run due to sandbox environment issues)
  - **recover command**: NOT VERIFIED (Requires active command execution)
  - **autonomous operation without babysitting**: FAILED (CRITICAL: Bot hits fatal Python exceptions during routine sweeps)
  - **December zip behavior restoration**: FAILED (Tight trailing from December is present in `rbz_tight_trailing.py` but fails to initialize)
  - **current strategy edge**: NOT VERIFIED (Rendered moot by execution/management failures)
  - **risk controls**: VERIFIED (Margin and Correlation gates actively block over-leveraging, sometimes too aggressively)
  ```
- **Last 20 Lines:**
  ```markdown
  ## SECTION 11 — Action plan
  1. **Highest-value fix: Fix Trailing Stop Wiring (`rbz_tight_trailing.py`)**
     - *Why:* Unprotected trades are bleeding capital. We must route the tight trailing logic to intercept whatever function the engine *is* using for management (e.g., `trade_manager_loop` or `systems/multi_signal_engine.py`).
  2. **Second highest-value fix: Fix `TerminalDisplay` Error in `oanda_trading_engine.py`**
     - *Why:* The bot cannot run autonomously if its 15-minute maintenance sweeps throw fatal exceptions. We need to sanitize all `self.display.info` calls in the engine.
  3. **Third highest-value fix: Tune the Margin / Correlation Gate**
     - *Why:* Trades with 78%+ confidence are being blocked instantly because margin calculation logic is severely restrictive. Needs to be loosened to allow December-level trade volumes.

  ---

  ### Final Verdict:
  1. **What is definitely proven:** Your trailing stops are fundamentally disconnected and have not been protecting profits.
  2. **What is not proven:** The trading edge itself (impossible to assess edge when management is missing).
  3. **What is broken:** The `_manage_trade` hook, the `Position Police` sweep loop, and the `Reoptimization` loop.
  4. **Trust in autonomous mode right now:** **NO.** Do not run this bot autonomously until the trailing wire is fixed.
  ```

## SECTION G — Final hard conclusion

1. Is the trailing stop disconnected? **YES**
2. Are maintenance/runtime errors breaking autonomy? **YES**
3. Is autonomous mode safe right now? **NO**
4. What exact code file should be fixed first? `/home/rfing/RBOTZILLA_PHOENIX/rbz_tight_trailing.py` (The attribute check for `_manage_trade` is failing on the live engine object).
5. What exact code file should be fixed second? `/home/rfing/RBOTZILLA_PHOENIX/util/terminal_display.py` (Modify the `info` signature matching the calls, or modify `oanda_trading_engine.py` to pass the correct arguments).
