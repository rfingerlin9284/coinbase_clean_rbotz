# Deep Audit of the Copilot “Operator-Run” Prompt Against the RBOTZILLA_PHOENIX Reality

## Scope and primary evidence used

This research cross-checks the behavior implied by the “operator-run” prompt (repo identity checks, runtime/log/process verification, dashboard binding verification, and minimal targeted fixes) against what is actually implemented in the **rfingerlin9284/rbotzilla_pheonix** repository’s operational entry points, runtime supervisors, and monitoring/logging utilities. Evidence is drawn directly from repository source files (shell scripts, Python modules, and operational docs) and a small set of official product/documentation sources for GitHub Copilot Agent Mode, WSL networking, and Flask-SocketIO host binding semantics. fileciteturn5file0L1-L1 fileciteturn13file0L1-L1 citeturn3search1turn5search1turn1search1

A key limitation: the transcript you pasted includes **local** edits (e.g., chmod calls; patching local tasks/docs) that are not necessarily reflected in the GitHub repo snapshot. This report therefore treats the repo as the “ground truth” for what is currently committed, and flags areas where the transcript’s conclusions conflict with what the repo shows. fileciteturn8file0L1-L1 fileciteturn9file0L1-L1

## What the prompt is trying to enforce, and why it’s a reasonable shape

Your prompt’s structure is conceptually sound for high-risk automation (especially anything that can place orders): it forces (a) a repo identity proof, (b) an operator-run workflow (agent writes, you run, agent analyzes), and (c) a “verify-and-fix mismatches” pass across entry points, log paths, process names, and bind addresses.

This is aligned with how **Copilot Agent Mode** is intended to work: it can autonomously search the codebase, propose edits, and suggest terminal commands; you stay in control by reviewing changes and confirming terminal command execution. GitHub’s own guidance describes agent mode as a multi-step loop (plan → edit → run checks → remediate → repeat) that can span multiple files and tools. citeturn3search1turn3search2turn3search0

Two practical friction points (also visible in your transcript) are common with agentic IDE workflows:

- Agents will often generate internal “task lists/todos” as part of their planning loop, even if you ask them not to. This is consistent with agent mode being designed around multi-step execution and iterative remediation. citeturn3search2turn3search1  
- Agents may auto-trigger build/tasks unless explicitly disabled; GitHub documents a setting to disable agent-run build tasks (`github.copilot.chat.agent.runTasks`). citeturn3search0

## What the repo already provides for operator workflows

Your prompt asked Copilot to “build/verify an operator package” (preflight/watch/collect/stop). The repository already includes a fairly extensive operator control surface, centered on **scripts/rbot_ctl.sh**, plus multiple “entry points” that start the engine in different ways.

### Main operator control script

`scripts/rbot_ctl.sh` is a comprehensive control interface that covers start/stop/restart/status/log tailing/narration viewing/monitoring and mode switching. It also defines an explicit headless log location and a PID file location. fileciteturn13file0L1-L1

Notable operational facts from this script:

- The headless runtime log path is set to `logs/oanda_headless.log` and the PID file is `/tmp/rbotzilla_oanda.pid`. fileciteturn13file0L1-L1  
- The “start” command launches `headless_runtime.py --broker all` under `nohup` and redirects stdout/stderr into that headless log. fileciteturn13file0L1-L1  
- The “stop” command kills the supervisor PID (if present), and also `pkill`s `oanda_trading_engine.py` and `headless_runtime.py` processes. fileciteturn13file0L1-L1  
- The “preflight” command runs a stop-loss QC test (`scripts/qc_sl_test.py --live-fire`) and then kicks off automated git/backup sync steps in the background. That’s powerful but not “minimal,” and it’s important to understand it before adopting it as a practice-session preflight routine. fileciteturn13file0L1-L1

### Engine entry points and how they differ

There are two primary “start” styles:

- **Foreground, interactive**: `start_trading.sh` activates the venv and runs `python -u oanda_trading_engine.py --env practice` (or `--env live --yes-live` after an explicit interactive confirmation). fileciteturn5file0L1-L1  
- **Headless supervisor**: `headless_runtime.py` spawns OANDA (and optionally Coinbase) as child processes and writes broker-specific logs under `logs/` (e.g., `logs/oanda_headless.log`). fileciteturn34file0L1-L1

This distinction matters because any “watch/collect evidence” scripts must either:
- watch the *foreground* console stream (usually captured by `tee`), or  
- watch the *headless* log files (`logs/*_headless.log`). fileciteturn5file0L1-L1 fileciteturn34file0L1-L1

### Mode selection and “practice vs live” truth source

The repository’s canonical mode system is **util/mode_manager.py**, which stores mode in `configs/runtime_mode.json` and enforces a PIN for switching to `LIVE`. Default state is `PAPER`. fileciteturn15file0L1-L1

The headless supervisor (`headless_runtime.py`) reads this mode and chooses `--env practice` for OANDA when mode is `PAPER`, and `--env live --yes-live` when mode is `LIVE`. fileciteturn34file0L1-L1

This is important because parts of your prompt (and the transcript) focus on `.env` fields like `OANDA_ACCOUNT_TYPE=live`. In this repo snapshot, “practice vs live” is not determined by an `OANDA_ACCOUNT_TYPE` flag; it is primarily driven by `configs/runtime_mode.json` (plus which token/account variables are actually set). fileciteturn15file0L1-L1 fileciteturn35file0L1-L1

## Findings that conflict with the transcript’s conclusions

Your transcript ends with Copilot asserting: “dashboard binds align to 127.0.0.1 (8080, 5001).” The committed repo snapshot does **not** align with that.

### Web dashboard bind addresses are `0.0.0.0` in the repo

- `dashboard/app_enhanced.py` calls `socketio.run(app, host='0.0.0.0', port=8080, ...)`. fileciteturn8file0L1-L1  
- `dashboard/websocket_server.py` calls `socketio.run(app, host='0.0.0.0', port=5001, ...)`. fileciteturn9file0L1-L1  

So, as committed, both servers listen on all interfaces, not just loopback. That is a direct mismatch with a “localhost-only” requirement.

This also matters because Flask-SocketIO’s documented default host is `127.0.0.1`; choosing `0.0.0.0` is a deliberate decision to listen on all network interfaces. citeturn1search1turn1search0

### Web dashboard code appears incomplete as committed

Both `dashboard/app_enhanced.py` and `dashboard/websocket_server.py` reference `request.sid` inside Socket.IO event handlers, but neither file imports `request` from Flask. As written, the first client connection event would raise a `NameError` unless something else injects `request` (which is not typical). fileciteturn8file0L1-L1 fileciteturn9file0L1-L1

This creates a second “mismatch class” your prompt intended to catch: not just host/port, but runtime correctness.

### Narration path contradictions are real, but not localized to VS Code tasks

Your transcript says Copilot found “narration.jsonl root vs logs/narration.jsonl in a task.” In the current repo snapshot:

- The narration logger writes to **repo root** `narration.jsonl` (`NARRATION_FILE = PROJECT_ROOT / "narration.jsonl"`). fileciteturn11file0L1-L1  
- The VS Code task “🗣️ Narration JSON (Raw Stream)” tails **root** `narration.jsonl`. fileciteturn12file0L1-L1  

However, contradictions still exist across documentation and configuration examples:

- `STARTUP_GUIDE.md` instructs `tail -f logs/narration.jsonl`. fileciteturn21file0L1-L1  
- `WORKFLOWS.md` repeatedly assumes `logs/narration.jsonl` and even suggests `streamlit run dashboard/app_enhanced.py` (but that file is Flask-SocketIO, not Streamlit). fileciteturn32file0L1-L1 fileciteturn8file0L1-L1  
- `MEGA_PROMPT.md` claims `util/narration_logger.py` writes to `logs/narration.jsonl`, but the code writes to root `narration.jsonl`. fileciteturn31file0L1-L1 fileciteturn11file0L1-L1  
- `.env.example` includes `NARRATION_FILE_OVERRIDE=logs/narration.jsonl`, but no code reference to `NARRATION_FILE_OVERRIDE` appears elsewhere in the repository snapshot, making this override effectively dead unless other branches/files exist outside the snapshot. fileciteturn35file0L1-L1

A robust operator “watch/evidence” script should use the same approach that `scripts/rbot_ctl.sh monitor` uses: prefer `narration.jsonl` at root and fall back to `logs/narration.jsonl` if needed. fileciteturn13file0L1-L1

## WSL implications of choosing `0.0.0.0` versus `127.0.0.1`

If your goal is “dashboard only visible locally,” binding to `127.0.0.1` is the standard pattern for Flask-SocketIO because its default host is `127.0.0.1` and `0.0.0.0` explicitly listens on all interfaces. citeturn1search1turn1search0

In WSL2 specifically, Windows-to-WSL localhost connectivity is commonly enabled, but the exact behavior depends on WSL networking mode and configuration. Microsoft documents a global `.wslconfig` setting `localhostForwarding` (default `true`) that controls whether ports bound to wildcard or localhost in the WSL VM are connectable from the Windows host via `localhost:port`. citeturn5search1

Microsoft also documents “mirrored mode networking” (`networkingMode=mirrored`) as a newer architecture for improved VPN compatibility and localhost behaviors. citeturn5search0turn5search1

The takeaway for your operator package is that **binding dashboards to `127.0.0.1` can still be compatible with Windows access in many modern WSL configurations**, while reducing the risk of exposing services beyond the local host interfaces. But if you do require LAN access (e.g., view dashboard from another device), then binding to `0.0.0.0` is the common technique—paired with OS firewall rules and explicit exposure controls. citeturn5search4turn1search1

## What a “minimal, correct” operator-run package should align to in this repo

Your prompt asked for preflight/watch/collect/stop scripts. In this repository, the minimum stable alignment points are already clearly defined by the existing operator interface and docs:

- For starting/stopping in a way that matches the repo’s “recommended ops,” use `scripts/rbot_ctl.sh start` and `scripts/rbot_ctl.sh stop`. fileciteturn14file0L1-L1  
- For headless logs, the authoritative file is `logs/oanda_headless.log` (for OANDA), created by `headless_runtime.py` and referenced by `rbot_ctl.sh`. fileciteturn34file0L1-L1 fileciteturn13file0L1-L1  
- For narration, the authoritative writer (`util/narration_logger.py`) targets `narration.jsonl` at repo root, and both the terminal dashboard (`dashboard.py`) and VS Code task definitions use root narration. fileciteturn11file0L1-L1 fileciteturn33file0L1-L1 fileciteturn12file0L1-L1  
- The “fallback stop” script is `turn_off.sh`, which attempts orchestrator shutdown, engine shutdown, and tmux session termination under a session name (`rbot_engine`). fileciteturn6file0L1-L1  

A small but important nuance: your transcript’s workflow focuses on `start_trading.sh practice` piped into `tee`. That is compatible with “foreground mode” and yields a clean `practice_session.log`, but it is not what the repository’s own Operations Guide calls the “primary control interface.” The guide explicitly points to `rbot_ctl.sh` as the core operator interface. fileciteturn14file0L1-L1 fileciteturn5file0L1-L1  

## How to tighten the prompt so agents comply more reliably

Two repo-backed improvements and two platform-backed improvements stand out.

### Make the prompt’s “truth source” explicit

Right now, “practice vs live” checks in many ad‑hoc operator scripts tend to look for `.env` strings. In this repo, the mode truth source is `configs/runtime_mode.json` managed by `util/mode_manager.py`, and headless runtime derives OANDA env flags from it. Tightening the prompt to require the agent to read and quote the mode manager logic reduces accidental misunderstandings. fileciteturn15file0L1-L1 fileciteturn34file0L1-L1

### Require evidence for bind-address claims

Given the repo’s current dashboard code binds to `0.0.0.0`, any agent claim that dashboards are localhost-only should be rejected unless it cites the exact `socketio.run(...host=...)` line. The Flask-SocketIO docs make the meaning of the host parameter unambiguous (default loopback vs wildcard). fileciteturn8file0L1-L1 fileciteturn9file0L1-L1 citeturn1search1

### Disable auto-running tasks when needed

If you want strict operator-run mode (agent suggests; human runs), you should explicitly disable Copilot’s ability to auto-run build tasks, since GitHub states agent mode can run build tasks automatically and documents a setting to disable this (`github.copilot.chat.agent.runTasks`). citeturn3search0

### Use “prompt files” to standardize operator constraints

GitHub has promoted “prompt files” (reusable markdown instructions in a workspace) as a way to keep agent behavior consistent across sessions. This matches your goal (“mega prompts and scripts you can hand to them”) and helps ensure every agent starts from the same non-negotiable rules. citeturn0search0turn3search0