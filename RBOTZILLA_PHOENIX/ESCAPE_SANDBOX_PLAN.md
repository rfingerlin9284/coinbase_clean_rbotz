# ESCAPE SANDBOX PLAN

## ROOT CAUSE ANALYSIS

### What is the sandbox?
The `nsjail` wrapper is **NOT** caused by your repo, your working directory, your scripts, or your terminal session. It is an **agent-infrastructure security layer** injected by the AI platform (Antigravity) that wraps every `run_command` call I make. Every command I issue — even `pwd` — gets routed through `/tmp/nsjail-sandbox-*/nsjail`, which is broken on your host because the required `nsjail` binary is missing from the expected path.

### Root Cause Table

| Test | What was tried | What happened | Conclusion |
|---|---|---|---|
| `pwd` from agent | Simplest possible command | `nsjail: cannot execute: required file not found` | Not repo-related |
| `/usr/bin/python3 --version` from agent | Absolute path binary | Same nsjail failure | Not binary-related |
| `./start_trading.sh practice` from agent | Repo script | Same nsjail failure | Not script-related |
| `./run_validation.sh` from USER terminal | Exact same repo, same scripts | ✅ ALL PASS | Repo is clean |
| `python3 verification_harness/validate_trailing.py` from USER terminal | Same harness, same venv | ✅ 9/9 PASS | Code is clean |
| `python3 -u oanda_trading_engine.py --env practice` from USER terminal | Same engine, same .env | ✅ Clean boot, trades placed | Engine is clean |

### Verdict
The sandbox is tied to **my agent process exclusively**. Your repo, your scripts, your venv, your terminal — all work perfectly. There is nothing to escape from on your side.

---

## WHY MOVING REPOS WILL NOT HELP

Creating a sibling copy, cloning to a new directory, or recreating the repo **will have zero effect** on this issue. The nsjail wrapper is injected by the AI agent runtime, not by anything in your filesystem. Proof: `pwd` fails. There is no simpler command and no repo involved.

---

## THE ACTUAL SOLUTION

There is no sandbox to escape. Your system works. The constraint is exclusively on the AI agent's command execution tool.

### How to operate going forward:

**You run commands. I write code and analyze output.**

This division of labor is the only path that works given the platform constraint:

1. **I** write/edit code, scripts, harnesses, config files
2. **You** execute them in your native terminal
3. **You** paste output back (or I read log files from disk)
4. **I** analyze results and iterate

---

## OPERATIONAL COMMANDS

### To start autonomous PRACTICE trading right now:
```bash
cd ~/RBOTZILLA_PHOENIX
source venv/bin/activate
./start_trading.sh practice
```

### To rerun the full validation suite:
```bash
cd ~/RBOTZILLA_PHOENIX
source venv/bin/activate
./run_validation.sh
```

### To check the dashboard after bot is running:
Open browser to `http://127.0.0.1:8080`

### To stop the bot:
```bash
./turn_off.sh
```

### To back up current state before any future changes:
```bash
cd ~/RBOTZILLA_PHOENIX
git add -A
git commit -m "Post-audit: all validation phases PASS - $(date -Iseconds)"
git push origin main
```

---

## HONEST FINAL ANSWERS

1. **Is the sandbox issue definitely caused by this repo?** NO — it affects every command including `pwd`
2. **Is moving to a new repo required?** NO — your repo is clean and validated
3. **Is creating a clean sibling copy the best next step?** NO — it will not fix anything
4. **Is there a lower-risk fix than moving repos entirely?** YES — do not move repos at all; the repo is not the problem
5. **What exact next command should I run first?**

```bash
cd ~/RBOTZILLA_PHOENIX && source venv/bin/activate && ./start_trading.sh practice
```
