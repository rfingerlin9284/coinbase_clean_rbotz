#!/usr/bin/env python3
"""
RBOTZILLA LIVE DASHBOARD
A persistent, human-readable terminal dashboard showing all bot activity.
Runs automatically when the bot starts. Pure Python/stdlib — no TALIB.
"""

import curses
import json
import os
import time
import glob
from datetime import datetime, timezone
from pathlib import Path

# ────────────────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────────────────
SCRIPT_DIR      = Path(__file__).parent
NARRATION_LOG   = SCRIPT_DIR / "narration.jsonl"
REGISTRY_DIR    = SCRIPT_DIR / "portfolio_registry"
REFRESH_SECONDS = 4   # How often the screen refreshes

# ────────────────────────────────────────────────────────────
# PLAIN-ENGLISH TRANSLATION OF EVENT TYPES
# ────────────────────────────────────────────────────────────
EVENT_LABELS = {
    "OCO_PLACED":               "📋 New trade order placed",
    "OCO_ERROR":                "⚠️  Trade order failed",
    "ORDER_REJECTED_MIN_NOTIONAL": "🚫 Order too small — rejected",
    "CHARTER_VIOLATION":        "⚠️  Rule violation detected",
    "RED_ALERT":                "🚨 LOSING trade — emergency exit",
    "SL_MOVED_BE":              "🔒 Stop Loss moved to protect profit",
    "SL_MOVED_TRAIL":           "📈 Stop Loss trailing a winner",
    "HIVE_ANALYSIS":            "🧠 Signal analysis complete",
    "ML_SIGNAL_APPROVED":       "✅ Signal approved — looking good",
    "ML_SIGNAL_REJECTED":       "❌ Signal rejected — not strong enough",
    "CONNECTION_LOST":          "🔌 Lost connection to broker",
    "CONNECTION_RESTORED":      "🔌 Reconnected to broker",
    "ENGINE_START":             "🚀 Bot engine started",
    "TRADE_OPENED":             "💰 Trade OPENED",
    "TRADE_CLOSED":             "🏁 Trade CLOSED",
    "POSITION_CLOSED":          "🏁 Position CLOSED",
    "TP_HIT":                   "🎯 TAKE PROFIT hit — winner!",
    "SL_HIT":                   "🛑 Stop Loss hit — small loss",
    "OCO_REQUIRED":             "⚠️  Order needs Stop + Target set",
}

def translate_event(event_type: str, details: dict, symbol: str) -> str:
    label = EVENT_LABELS.get(event_type, f"ℹ️  {event_type.replace('_', ' ').title()}")
    sym   = symbol if symbol and symbol != "SYSTEM" else ""
    pair  = f" [{sym}]" if sym else ""

    # Extra plain-English detail for key events
    if event_type == "SL_MOVED_BE":
        old_sl = details.get("new_sl") or details.get("green_floor", "")
        return f"{label}{pair}  →  Stop now at {old_sl:.5f}" if old_sl else f"{label}{pair}"
    if event_type == "HIVE_ANALYSIS":
        conf  = details.get("confidence", 0)
        cons  = details.get("consensus", "?").upper()
        return f"{label}{pair}  →  Wants to {cons} (confidence {conf*100:.0f}%)"
    if event_type in ("TRADE_OPENED", "OCO_PLACED"):
        entry = details.get("entry_price") or details.get("entry")
        sl    = details.get("stop_loss")
        tp    = details.get("take_profit")
        direction = details.get("direction", "")
        parts = []
        if direction: parts.append(direction)
        if entry: parts.append(f"@ {entry}")
        if sl: parts.append(f"Stop:{sl}")
        if tp: parts.append(f"Target:{tp}")
        extra = "  →  " + "  ".join(parts) if parts else ""
        return f"{label}{pair}{extra}"
    if event_type in ("TRADE_CLOSED", "POSITION_CLOSED", "TP_HIT", "SL_HIT"):
        pnl = details.get("pnl_usd") or details.get("pnl")
        if pnl is not None:
            sign = "+" if float(pnl) >= 0 else ""
            return f"{label}{pair}  →  P&L: {sign}${float(pnl):.2f}"
    if event_type == "RED_ALERT":
        loss = details.get("pnl_percent") or details.get("pnl")
        if loss is not None:
            return f"{label}{pair}  →  Loss: {float(loss):.2f}% — exiting now"
    return f"{label}{pair}"


# ────────────────────────────────────────────────────────────
# DATA READERS
# ────────────────────────────────────────────────────────────
def read_recent_events(n=20):
    """Read the last N events from narration.jsonl."""
    events = []
    try:
        if not NARRATION_LOG.exists():
            return events
        with open(NARRATION_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                ts_raw = ev.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    # Convert to local time display
                    ts = dt.strftime("%I:%M:%S %p")
                except Exception:
                    ts = ts_raw[:19].replace("T", " ")
                events.append({
                    "ts":      ts,
                    "type":    ev.get("event_type", ""),
                    "symbol":  ev.get("symbol", ""),
                    "details": ev.get("details", {}),
                    "text":    translate_event(ev.get("event_type",""), ev.get("details",{}), ev.get("symbol",""))
                })
                if len(events) >= n:
                    break
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return events


def read_open_positions():
    """Read open positions from portfolio_registry JSON files."""
    positions = []
    try:
        if not REGISTRY_DIR.exists():
            return positions
        for f in sorted(REGISTRY_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                status = data.get("status", "").lower()
                if status in ("open", "opening", "active"):
                    positions.append(data)
            except Exception:
                continue
    except Exception:
        pass
    return positions


def bot_is_running() -> bool:
    """Check if the orchestrator process is running."""
    try:
        result = os.popen("pgrep -f orchestrator_start.py").read().strip()
        return bool(result)
    except Exception:
        return False


def format_position_lines(pos: dict) -> list:
    """Turn a raw position dict into 2 plain-English display lines."""
    sym     = pos.get("symbol", "???")
    units   = pos.get("size_units", 0)
    direction = "BUY  ↑" if float(units) > 0 else "SELL ↓"
    entry   = pos.get("entry_price", 0)
    sl      = pos.get("current_sl", 0)
    tp      = pos.get("take_profit", 0)
    metrics = pos.get("metrics", {}) or {}
    cur     = metrics.get("current_price") or entry
    pnl     = metrics.get("pnl_usd", 0) or 0
    pnl_p   = metrics.get("pnl_percent", 0) or 0
    sign    = "+" if float(pnl) >= 0 else ""
    emoji   = "✅" if float(pnl) >= 0 else "🔴"
    sl_mode = pos.get("sl_mode", "").replace("_", " ").upper()

    line1 = (f"  {emoji} {sym:10s}  {direction}  |  Entry: {entry:.5f}  "
             f"Now: {cur:.5f}  |  P&L: {sign}${float(pnl):.2f}  ({sign}{float(pnl_p):.2f}%)")
    line2 = (f"     Stop Loss: {float(sl):.5f}   Take Profit: {float(tp):.5f}   "
             f"SL Mode: {sl_mode if sl_mode else 'INITIAL'}")
    return [line1, line2]


# ────────────────────────────────────────────────────────────
# CURSES DASHBOARD
# ────────────────────────────────────────────────────────────
def run_dashboard(stdscr):
    curses.curs_set(0)   # hide cursor
    stdscr.nodelay(True) # non-blocking key input
    curses.start_color()
    curses.use_default_colors()

    # Colour pairs
    curses.init_pair(1, curses.COLOR_CYAN,    -1)  # title / borders
    curses.init_pair(2, curses.COLOR_GREEN,   -1)  # good / profit
    curses.init_pair(3, curses.COLOR_RED,     -1)  # bad / loss
    curses.init_pair(4, curses.COLOR_YELLOW,  -1)  # warning / neutral
    curses.init_pair(5, curses.COLOR_WHITE,   -1)  # normal text
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)  # section headers

    C_TITLE  = curses.color_pair(1) | curses.A_BOLD
    C_GOOD   = curses.color_pair(2)
    C_BAD    = curses.color_pair(3)
    C_WARN   = curses.color_pair(4)
    C_NORM   = curses.color_pair(5)
    C_HEAD   = curses.color_pair(6) | curses.A_BOLD

    start_time = time.time()

    while True:
        # Quit on 'q'
        key = stdscr.getch()
        if key == ord('q'):
            break

        stdscr.erase()
        rows, cols = stdscr.getmaxyx()
        now_str = datetime.now().strftime("%Y-%m-%d  %I:%M:%S %p")
        running = bot_is_running()
        uptime_secs = int(time.time() - start_time)
        uptime_str  = f"{uptime_secs // 3600}h {(uptime_secs % 3600) // 60}m {uptime_secs % 60}s"

        row = 0

        # ── TITLE BAR ─────────────────────────────────────────────
        title = "  🤖  RBOTZILLA PHOENIX — LIVE TRADING DASHBOARD"
        stdscr.addstr(row, 0, title.ljust(cols), C_TITLE)
        row += 1
        sub = f"  Updated: {now_str}    Dashboard uptime: {uptime_str}    Press Q to close"
        stdscr.addstr(row, 0, sub[:cols].ljust(cols), C_NORM)
        row += 1
        stdscr.addstr(row, 0, "─" * cols, C_TITLE)
        row += 1

        # ── BOT STATUS ────────────────────────────────────────────
        if running:
            status_str = "🟢  BOT IS RUNNING — Trading autonomously"
            stdscr.addstr(row, 0, f"  {status_str}", C_GOOD | curses.A_BOLD)
        else:
            status_str = "🔴  BOT IS STOPPED — Run ./turn_on.sh to start"
            stdscr.addstr(row, 0, f"  {status_str}", C_BAD | curses.A_BOLD)
        row += 2

        # ── OPEN POSITIONS ────────────────────────────────────────
        positions = read_open_positions()
        stdscr.addstr(row, 0, "  📊  OPEN POSITIONS", C_HEAD)
        row += 1
        stdscr.addstr(row, 0, "  " + "─" * (cols - 4), C_TITLE)
        row += 1

        if not positions:
            stdscr.addstr(row, 0, "  No open positions right now — bot is scanning for opportunities.", C_WARN)
            row += 1
        else:
            for pos in positions:
                plines = format_position_lines(pos)
                for pl in plines:
                    if row >= rows - 2:
                        break
                    pnl_val = (pos.get("metrics") or {}).get("pnl_usd", 0) or 0
                    colour = C_GOOD if float(pnl_val) >= 0 else C_BAD
                    stdscr.addstr(row, 0, pl[:cols], colour)
                    row += 1
                row += 1  # blank line between positions

        if row < rows - 2:
            stdscr.addstr(row, 0, "─" * cols, C_TITLE)
            row += 1

        # ── RECENT ACTIVITY ───────────────────────────────────────
        if row < rows - 2:
            stdscr.addstr(row, 0, "  📜  RECENT ACTIVITY  (newest first)", C_HEAD)
            row += 1
            if row < rows - 2:
                stdscr.addstr(row, 0, "  " + "─" * (cols - 4), C_TITLE)
                row += 1

        events = read_recent_events(n=rows - row - 2)
        for ev in events:
            if row >= rows - 2:
                break
            ev_type = ev["type"]
            ts      = ev["ts"]
            text    = ev["text"]

            # Colour code by event type
            if any(k in ev_type for k in ("ERROR","VIOLATION","RED_ALERT","REJECTED","LOST","SL_HIT")):
                colour = C_BAD
            elif any(k in ev_type for k in ("TP_HIT","APPROVED","OPENED","RESTORED","PLACED")):
                colour = C_GOOD
            elif any(k in ev_type for k in ("SL_MOVED","TRAIL","START","REALLOC")):
                colour = C_WARN
            else:
                colour = C_NORM

            line = f"  {ts}   {text}"
            stdscr.addstr(row, 0, line[:cols], colour)
            row += 1

        # ── FOOTER ────────────────────────────────────────────────
        if rows > 3:
            footer = "  Q = quit dashboard  |  Bot keeps running in the background  |  ./turn_off.sh to stop bot"
            stdscr.addstr(rows - 1, 0, footer[:cols].ljust(cols), C_TITLE)

        stdscr.refresh()
        time.sleep(REFRESH_SECONDS)


def main():
    print("Starting RBOTZILLA Dashboard... press Q to exit (bot keeps running).")
    time.sleep(1)
    curses.wrapper(run_dashboard)
    print("Dashboard closed. Bot is still running in the background.")
    print("To stop the bot run:  ./turn_off.sh")


if __name__ == "__main__":
    main()
