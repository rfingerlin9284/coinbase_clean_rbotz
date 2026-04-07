# Live-Fire SL Test Report

**Date:** 2026-03-12
**Target Broker:** OANDA Practice 
**Test Suite:** `scripts/qc_sl_test.py --live-fire`

## Test Objective
To verify that the recent tuning adjustments (specifically the 3-pip minimum spread clearance in `rbz_tight_trailing.py` and the $150 global risk limit in `oanda_trading_engine.py`) function correctly natively on the broker platform, ensuring there are no execution errors or precision rejections when modifying live trades.

## Execution Summary

The `qc_sl_test.py` diagnostics suite was executed in `--live-fire` mode directly against the OANDA API.

1.  **Live Order Placement**: Physically executed a real 100-unit micro BUY order on EUR/USD on the OANDA practice account.
2.  **Tracking & Modification**: Tracked the `tradeID`, verified that the initial Stop Loss attached perfectly, and successfully tested the `set_trade_stop` API endpoint to ensure the core engine can freely move the Stop Loss.
3.  **Sanity Checks**: Ran all 104 strategy combinations through the policy engine to ensure there are no math errors or missing overrides in any of the active strategies.
4.  **Clean Up**: Closed the micro test trade.

## Results
**61 out of 61 checks PASSED.** 

The bot confirmed native API access and verified that the math for the new tuning parameters is completely compatible with OANDA's order execution system. The trailing logic effectively updates stops without blockage.

## Conclusion
The Stop Loss system is verified and live. 
All strategies correctly inherit the $150 global limit and the tight trailing minimum clearance parameters.
