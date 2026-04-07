#!/usr/bin/env bash
set -euo pipefail

REPO="/home/rfing/RBOTZILLA_PHOENIX"
cd "$REPO"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$REPO/.operator_fix_backups/$STAMP"
mkdir -p "$BACKUP_DIR" scripts logs .vscode

say() { printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

backup_if_exists() {
  local f="$1"
  if [ -f "$f" ]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$f")"
    cp -f "$f" "$BACKUP_DIR/$f"
  fi
}

say "Repo truth check"
pwd
git rev-parse --show-toplevel || true
git remote -v || true
git branch --show-current || true
git status --short --branch || true

for f in \
  dashboard/app_enhanced.py \
  dashboard/websocket_server.py \
  .vscode/tasks.json \
  STARTUP_GUIDE.md \
  WORKFLOWS.md \
  MEGA_PROMPT.md \
  .env.example \
  NATIVE_EVIDENCE_LEDGER.md \
  PRACTICE_SESSION_1_CHECKLIST.md \
  PRACTICE_ABORT_RULES.md \
  PRACTICE_SESSION_1_OPERATOR_BLOCKS.md \
  scripts/preflight_practice_session.sh \
  scripts/watch_practice_session.sh \
  scripts/collect_practice_session_evidence.sh \
  scripts/stop_practice_session.sh
 do
  backup_if_exists "$f"
done

say "Patching dashboard host/import issues and narration task fallback"
python3 <<'PY'
from pathlib import Path
import json
import re
import sys

repo = Path("/home/rfing/RBOTZILLA_PHOENIX")

def patch_request_and_host(path_str: str):
    p = repo / path_str
    if not p.exists():
        return
    s = p.read_text()

    if "request.sid" in s and "from flask import Flask, request" not in s:
        s = s.replace("from flask import Flask", "from flask import Flask, request")

    if "socketio.run(" in s:
        s = re.sub(
            r"socketio\.run\(([^)]*?)host\s*=\s*['\"](?:0\.0\.0\.0|127\.0\.0\.1)['\"]",
            r"socketio.run(\1host=os.getenv('RBZ_DASH_HOST', '127.0.0.1')",
            s,
            count=1,
            flags=re.S,
        )

    if "RBZ_DASH_HOST" in s and "import os" not in s:
        lines = s.splitlines()
        insert_at = 0
        for i, line in enumerate(lines[:25]):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, "import os")
        s = "\n".join(lines) + ("\n" if not s.endswith("\n") else "")

    p.write_text(s)

for f in ["dashboard/app_enhanced.py", "dashboard/websocket_server.py"]:
    patch_request_and_host(f)

tasks = repo / ".vscode/tasks.json"
if tasks.exists():
    try:
        obj = json.loads(tasks.read_text())
        changed = False
        for task in obj.get("tasks", []):
            cmd = task.get("command")
            if isinstance(cmd, str) and "narration.jsonl" in cmd and "tail -f" in cmd:
                task["command"] = "bash -lc 'if [ -f narration.jsonl ]; then tail -f narration.jsonl; elif [ -f logs/narration.jsonl ]; then tail -f logs/narration.jsonl; else echo \"narration file not found\"; exit 1; fi'"
                changed = True
        if changed:
            tasks.write_text(json.dumps(obj, indent=2) + "\n")
    except Exception as e:
        print(f"WARNING: tasks.json not patched cleanly: {e}", file=sys.stderr)
PY

say "Writing operator scripts"

cat > scripts/preflight_practice_session.sh <<'BASH2'
#!/usr/bin/env bash
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
red()   { printf '\033[0;31m%s\033[0m\n' "$1"; }

check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    green "  PASS - ${label}"
    PASS=$((PASS+1))
  else
    red "  FAIL - ${label}"
    FAIL=$((FAIL+1))
  fi
}

echo "================================================================="
echo "PREFLIGHT - PRACTICE SESSION"
echo "Repo: $REPO"
echo "================================================================="

check "repo root exists" test -d "$REPO"
check "venv exists" test -d "$REPO/venv"
check "venv python exists" test -x "$REPO/venv/bin/python3"
check "start_trading.sh exists" test -f "$REPO/start_trading.sh"
check "turn_off.sh exists" test -f "$REPO/turn_off.sh"
check "scripts/watch_practice_session.sh exists" test -f "$REPO/scripts/watch_practice_session.sh"
check "scripts/collect_practice_session_evidence.sh exists" test -f "$REPO/scripts/collect_practice_session_evidence.sh"
check "scripts/stop_practice_session.sh exists" test -f "$REPO/scripts/stop_practice_session.sh"
check "dashboard app exists" test -f "$REPO/dashboard/app_enhanced.py"
check "dashboard websocket exists" test -f "$REPO/dashboard/websocket_server.py"
check "engine exists" test -f "$REPO/oanda_trading_engine.py"
check "tight trailing exists" test -f "$REPO/rbz_tight_trailing.py"
check "no stale engine process" bash -lc "! pgrep -f 'oanda_trading_engine.py' >/dev/null 2>&1"
check "dashboard app localhost default" grep -q "RBZ_DASH_HOST', '127.0.0.1'" "$REPO/dashboard/app_enhanced.py"
check "dashboard ws localhost default" grep -q "RBZ_DASH_HOST', '127.0.0.1'" "$REPO/dashboard/websocket_server.py"

if [ -f "$REPO/configs/runtime_mode.json" ]; then
  check "runtime mode file present" test -f "$REPO/configs/runtime_mode.json"
fi

mkdir -p "$REPO/logs"

echo "-----------------------------------------------------------------"
echo "RESULT: $PASS PASS / $FAIL FAIL"
echo "----------------------------------------------------------------="

if [ "$FAIL" -eq 0 ]; then
  green "READY FOR PRACTICE LAUNCH"
  exit 0
else
  red "FIX FAILURES BEFORE LAUNCH"
  exit 1
fi
BASH2

cat > scripts/watch_practice_session.sh <<'BASH2'
#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pick_log() {
  local best=""
  local best_mtime=0
  local candidates=(
    "$REPO/logs/practice_session.log"
    "$REPO/logs/oanda_headless.log"
    "$REPO/logs/native_boot_capture.log"
    "$REPO/logs/engine_stdout.log"
    "$REPO/nohup.out"
  )
  for f in "${candidates[@]}"; do
    if [ -f "$f" ]; then
      local m
      m=$(stat -c %Y "$f" 2>/dev/null || echo 0)
      if [ "$m" -gt "$best_mtime" ]; then
        best="$f"
        best_mtime="$m"
      fi
    fi
  done
  printf '%s' "$best"
}

LOG="$(pick_log)"
PID="$(pgrep -f 'oanda_trading_engine.py' | head -n 1 || true)"

echo "================================================================="
echo "PRACTICE SESSION WATCHER"
echo "Repo: $REPO"
echo "Log:  ${LOG:-NONE}"
echo "PID:  ${PID:-NOT RUNNING}"
echo "================================================================="

if [ -z "${LOG:-}" ]; then
  echo "No log found."
  echo "Launch with:"
  echo "./start_trading.sh practice 2>&1 | tee logs/practice_session.log"
  exit 1
fi

tail -n 50 -F "$LOG" | grep --line-buffered --color=always -iE \
'PRACTICE|PAPER TRADING|OPEN |OCO|TRADE MANAGER|SYNC|Synced existing|_manage_trade|_apply_tight_sl|TightSL|signal_type|mean_reversion|TRAIL|STEP1|STEP2|cooldown|MARKET SCAN|BLOCKED|ERROR|CRITICAL|Traceback|TypeError|AttributeError|Position opened|order placed'
BASH2

cat > scripts/collect_practice_session_evidence.sh <<'BASH2'
#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/PRACTICE_SESSION_1_EVIDENCE.md"

pick_log() {
  local best=""
  local best_mtime=0
  local candidates=(
    "$REPO/logs/practice_session.log"
    "$REPO/logs/oanda_headless.log"
    "$REPO/logs/native_boot_capture.log"
    "$REPO/logs/engine_stdout.log"
    "$REPO/nohup.out"
  )
  for f in "${candidates[@]}"; do
    if [ -f "$f" ]; then
      local m
      m=$(stat -c %Y "$f" 2>/dev/null || echo 0)
      if [ "$m" -gt "$best_mtime" ]; then
        best="$f"
        best_mtime="$m"
      fi
    fi
  done
  printf '%s' "$best"
}

LOG="$(pick_log)"
NARR=""
if [ -f "$REPO/narration.jsonl" ]; then
  NARR="$REPO/narration.jsonl"
elif [ -f "$REPO/logs/narration.jsonl" ]; then
  NARR="$REPO/logs/narration.jsonl"
fi

if [ -z "${LOG:-}" ]; then
  echo "No runtime log found." >&2
  exit 1
fi

extract() {
  local title="$1"
  local pattern="$2"
  echo "## $title"
  local found
  found="$(grep -iE "$pattern" "$LOG" | tail -n 12 || true)"
  if [ -n "$found" ]; then
    echo '```text'
    echo "$found"
    echo '```'
  else
    echo "NOT OBSERVED YET"
  fi
  echo
}

{
  echo "# PRACTICE SESSION 1 EVIDENCE"
  echo
  echo "- Collected: $(date -Iseconds)"
  echo "- Runtime log: $LOG"
  echo "- Narration log: ${NARR:-NOT FOUND}"
  echo

  extract "Startup Proof" "SYSTEM INITIALIZATION|Startup initiated|RBOTZILLA PHOENIX"
  extract "Practice Mode Proof" "PRACTICE|PAPER TRADING|Real Money: NO"
  extract "Trade Placement Proof" "OPEN .*@|Position opened|Placing .* order|TRADE_OPENED"
  extract "OCO Proof" "OCO order placed|TP/SL validated|OCO"
  extract "Trade Manager Proof" "TRADE MANAGER|ACTIVATED AND CONNECTED|manage"
  extract "Sync Recovery Proof" "Synced existing|sync_open_positions|Re-imported|orphan"
  extract "Trailing Management Proof" "_apply_tight_sl|TightSL|STEP1|STEP2|TRAIL|tight_step"
  extract "Signal Type Proof" "signal_type|mean_reversion|TRAIL_TIGHT|SCALE_OUT"
  extract "Errors Found" "Traceback|TypeError|AttributeError|KeyError|CRITICAL|ERROR"

  echo "## Narration Tail"
  if [ -n "${NARR:-}" ]; then
    echo '```text'
    tail -n 20 "$NARR" || true
    echo '```'
  else
    echo "NOT OBSERVED YET"
  fi
  echo

  echo "## SUMMARY"
  echo
  echo "### OBSERVED"
  grep -qiE "RBOTZILLA PHOENIX|Startup initiated" "$LOG" && echo "- startup" || true
  grep -qiE "PRACTICE|PAPER TRADING" "$LOG" && echo "- practice mode" || true
  grep -qiE "OPEN .*@|Position opened" "$LOG" && echo "- trade placement" || true
  grep -qiE "OCO order placed|TP/SL validated" "$LOG" && echo "- OCO" || true
  grep -qiE "TRADE MANAGER|ACTIVATED AND CONNECTED" "$LOG" && echo "- trade manager" || true
  grep -qiE "Synced existing|sync_open_positions|Re-imported" "$LOG" && echo "- sync/recovery" || true
  grep -qiE "_apply_tight_sl|TightSL|STEP1|STEP2|TRAIL" "$LOG" && echo "- trailing evidence" || true
  grep -qiE "signal_type|mean_reversion|TRAIL_TIGHT|SCALE_OUT" "$LOG" && echo "- signal_type evidence" || true
  echo
  echo "### NOT OBSERVED"
  grep -qiE "_manage_trade" "$LOG" || echo "- _manage_trade runtime marker"
  grep -qiE "_apply_tight_sl|TightSL|STEP1|STEP2|TRAIL" "$LOG" || echo "- trailing runtime marker"
  grep -qiE "signal_type|mean_reversion|TRAIL_TIGHT|SCALE_OUT" "$LOG" || echo "- signal_type runtime marker"
  echo
  echo "### NEEDS MORE RUNTIME"
  echo "- cooldown expiry and re-entry"
  echo "- full trade lifecycle close -> re-manage -> re-enter"
} > "$OUT"

echo "Wrote $OUT"
BASH2

cat > scripts/stop_practice_session.sh <<'BASH2'
#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STOPPED=0

echo "================================================================="
echo "STOP PRACTICE SESSION"
echo "================================================================="

if [ -f "$REPO/bot.pid" ]; then
  PID="$(cat "$REPO/bot.pid" 2>/dev/null || true)"
  if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    sleep 2
    kill -0 "$PID" 2>/dev/null && kill -9 "$PID" 2>/dev/null || true
    STOPPED=1
  fi
  rm -f "$REPO/bot.pid"
fi

if pgrep -f "oanda_trading_engine.py" >/dev/null 2>&1; then
  pkill -f "oanda_trading_engine.py" || true
  sleep 2
  pgrep -f "oanda_trading_engine.py" >/dev/null 2>&1 && pkill -9 -f "oanda_trading_engine.py" || true
  STOPPED=1
fi

if pgrep -f "headless_runtime.py" >/dev/null 2>&1; then
  pkill -f "headless_runtime.py" || true
  sleep 2
  pgrep -f "headless_runtime.py" >/dev/null 2>&1 && pkill -9 -f "headless_runtime.py" || true
  STOPPED=1
fi

if pgrep -f "orchestrator_start.py" >/dev/null 2>&1; then
  pkill -f "orchestrator_start.py" || true
  STOPPED=1
fi

if command -v tmux >/dev/null 2>&1; then
  tmux has-session -t rbot_engine 2>/dev/null && tmux kill-session -t rbot_engine || true
fi

if [ "$STOPPED" -eq 0 ] && [ -x "$REPO/turn_off.sh" ]; then
  bash "$REPO/turn_off.sh" || true
fi

echo
if pgrep -f "oanda_trading_engine.py|headless_runtime.py|orchestrator_start.py" >/dev/null 2>&1; then
  echo "WARNING: some matching processes still running"
  pgrep -af "oanda_trading_engine.py|headless_runtime.py|orchestrator_start.py" || true
else
  echo "Bot stopped cleanly."
fi
BASH2

chmod +x scripts/preflight_practice_session.sh \
         scripts/watch_practice_session.sh \
         scripts/collect_practice_session_evidence.sh \
         scripts/stop_practice_session.sh

say "Writing operator docs"

cat > NATIVE_EVIDENCE_LEDGER.md <<'MD'
# NATIVE EVIDENCE LEDGER

Last updated: pending next native run

## VERIFIED BY NATIVE OUTPUT
- Engine startup
- Practice mode
- Trade placement
- OCO placement
- Trade manager activation
- Sync/recovery
- Trailing progression via harness
- Signal type routing via harness
- Maintenance loop stability
- Dashboard localhost default (code grep + runtime expectation)

## STATIC CODE VERIFIED ONLY
- `_manage_trade` exists in engine
- `_apply_tight_sl` implementation present
- `signal_type` passed into management path
- Dashboard host defaults to localhost via `RBZ_DASH_HOST`
- Narration logger writes to repo-root `narration.jsonl`

## NOT VERIFIED YET
- `_manage_trade` runtime hit on real trade
- `_apply_tight_sl` runtime hit on real trade
- Real-trade `signal_type` routing evidence
- Cooldown expiry -> re-entry cycle
- Full autonomous practice cycle end-to-end
MD

cat > PRACTICE_SESSION_1_CHECKLIST.md <<'MD'
# PRACTICE SESSION 1 CHECKLIST

## Pre-Launch
- [ ] PASS / FAIL — repo is `/home/rfing/RBOTZILLA_PHOENIX`
- [ ] PASS / FAIL — venv active
- [ ] PASS / FAIL — preflight passed
- [ ] PASS / FAIL — practice mode only
- [ ] PASS / FAIL — no stale engine process

## Launch
- [ ] PASS / FAIL — bot launched
- [ ] PASS / FAIL — stdout captured to `logs/practice_session.log`
- [ ] PASS / FAIL — practice mode visible in output

## First Runtime Window
- [ ] PASS / FAIL — first market scan observed
- [ ] PASS / FAIL — first trade placed OR first blocked trade observed
- [ ] PASS / FAIL — OCO observed
- [ ] PASS / FAIL — trade manager observed
- [ ] PASS / FAIL — no traceback / TypeError / AttributeError observed

## Extended Runtime
- [ ] PASS / FAIL — dashboard reachable at localhost
- [ ] PASS / FAIL — evidence collected
- [ ] PASS / FAIL — last 100 log lines captured

## Shutdown
- [ ] PASS / FAIL — safe shutdown completed
- [ ] PASS / FAIL — no orphan engine processes remain
MD

cat > PRACTICE_ABORT_RULES.md <<'MD'
# PRACTICE ABORT RULES

Primary stop command:
```bash
cd ~/RBOTZILLA_PHOENIX
bash scripts/stop_practice_session.sh
```

Fallback:

```bash
cd ~/RBOTZILLA_PHOENIX
bash turn_off.sh || true
pkill -9 -f "oanda_trading_engine.py|headless_runtime.py|orchestrator_start.py" || true
```

| Trigger                    | What to look for                                                  |
| -------------------------- | ----------------------------------------------------------------- |
| Any traceback              | `Traceback (most recent call last):`                              |
| Live-account indicator     | `LIVE`, missing `PAPER TRADING`, unexpected `--yes-live` behavior |
| Repeated crash loop        | Same error 3+ times in 5 minutes                                  |
| Missing OCO                | A trade is placed, but the `hedge_fund_orchestrator` fails to log OCO creation |
| Runaway trade count        | abnormal rapid position growth                                    |
| Suspicious exposure        | huge notional / margin alarm / repeated guard breaches            |
| Dashboard exposure wrong   | dashboard starts on non-local bind when not intended              |
| TypeError / AttributeError | any old crash marker returns                                      |
MD

cat > PRACTICE_SESSION_1_OPERATOR_BLOCKS.md <<'MD'

# PRACTICE SESSION 1 — OPERATOR BLOCKS

## 1) PREFLIGHT

```bash
cd ~/RBOTZILLA_PHOENIX
source venv/bin/activate
bash scripts/preflight_practice_session.sh
```

## 2) LAUNCH

```bash
cd ~/RBOTZILLA_PHOENIX
source venv/bin/activate
mkdir -p logs
./start_trading.sh practice 2>&1 | tee logs/practice_session.log
```

## 3) WATCH (second terminal)

```bash
cd ~/RBOTZILLA_PHOENIX
bash scripts/watch_practice_session.sh
```

## 4) COLLECT EVIDENCE

```bash
cd ~/RBOTZILLA_PHOENIX
bash scripts/collect_practice_session_evidence.sh
cat PRACTICE_SESSION_1_EVIDENCE.md
tail -n 100 logs/practice_session.log
```

## 5) STOP

```bash
cd ~/RBOTZILLA_PHOENIX
bash scripts/stop_practice_session.sh
```

MD

say "Normalizing critical docs that referenced logs/narration.jsonl or Streamlit"
python3 <<'PY'
from pathlib import Path
repo = Path("/home/rfing/RBOTZILLA_PHOENIX")

replacements = {
    "STARTUP_GUIDE.md": [
        ("logs/narration.jsonl", "narration.jsonl"),
    ],
    "WORKFLOWS.md": [
        ("streamlit run dashboard/app_enhanced.py", "python dashboard/app_enhanced.py"),
        ("logs/narration.jsonl", "narration.jsonl"),
    ],
    "MEGA_PROMPT.md": [
        ("logs/narration.jsonl", "narration.jsonl"),
    ],
    ".env.example": [
        ("NARRATION_FILE_OVERRIDE=logs/narration.jsonl", "# NARRATION_FILE_OVERRIDE is not read by current code; narration defaults to repo-root narration.jsonl"),
    ],
}

for file_name, reps in replacements.items():
    p = repo / file_name
    if not p.exists():
        continue
    s = p.read_text()
    orig = s
    for a, b in reps:
        s = s.replace(a, b)
    if s != orig:
        p.write_text(s)
PY

say "Static syntax check"
python3 - <<'PY'
import py_compile
files = [
"dashboard/app_enhanced.py",
"dashboard/websocket_server.py",
]
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK: {f}")
    except Exception as e:
        print(f"WARNING: compile failed for {f}: {e}")
PY

say "Done"
echo
echo "Backups saved under: $BACKUP_DIR"
echo
echo "Run next:"
echo "  cd /home/rfing/RBOTZILLA_PHOENIX"
echo "  source venv/bin/activate"
echo "  bash scripts/preflight_practice_session.sh"
echo "  mkdir -p logs"
echo "  ./start_trading.sh practice 2>&1 | tee logs/practice_session.log"
echo
echo "Second terminal:"
echo "  cd /home/rfing/RBOTZILLA_PHOENIX"
echo "  bash scripts/watch_practice_session.sh"
