# Standalone Deployment Guide ✅

## Purpose

This document explains how to build, verify, and package a clean, standalone deployment of the RICK `MULTI_BROKER_PHOENIX` system that is ready for either **paper** or **live (real-money)** operation. The default and safe mode is **paper trading**; the only difference between paper and live is the API keys and endpoints — the logic, timing, autonomous agents, and all features are identical.

## Important safety note (non-negotiable)

- Your canonical `ops/secrets.env` will NOT be modified by any of the tools. It will be respected and preserved as-is.
- The pack-and-backup process can include `ops/secrets.env` in the final compressed archive if requested. If it contains real money keys, you are responsible for secure storage of that backup.

## Quick defaults

- Default mode on start: **paper trading** (safe). Launchers will require explicit opt-in to run in `real` mode.
- To run in `real` mode you must set the environment variable `ALLOW_REAL_LAUNCH=1` before invoking the launcher (no script edits to your `ops/secrets.env` are performed).

## What the build will produce

- A `deployment/` folder containing the minimal set of files required for a standalone run (scripts, `tools/`, key configs, and docs).
- A compressed artifact (tar.gz) named like `multi_broker_phoenix-deployment-<iso8601>.tar.gz`.
- A `release_manifest.json` listing every included file with SHA256 and size.
- A `build_report.json` listing excluded legacy files, duplicates found, and verification results.

## How legacy and duplicates are handled

- Legacy/duplicate files are NOT deleted from the repo. Instead, the build process will omit files that match harmless legacy patterns (e.g., `*old*`, `*backup*`, `*.bak`) and will list them in the `build_report.json` so you can review.

## Secrets & Mandatory Approval (non-negotiable)

- The canonical `ops/secrets.env` is treated as read-only and will never be modified by build or verify tools.
- **Including** `ops/secrets.env` in a deployment archive is only allowed after a mandatory approval step:
  - Use `tools/secure_env_manager.py set-pin` to set a local PIN (stored as a salted hash in `.secure/pin.hash`).
  - Use `tools/secure_env_manager.py approve --message "reason"` to create an approval id. This writes an approval file into `.secure/approvals/` and appends an entry into `HISTORICAL_CHANGE_LOG.md`.
  - The build script `tools/build_deployment.py` requires `--include-secrets --approval-id <id>` and will verify that the approval id exists in `HISTORICAL_CHANGE_LOG.md`.
- All approvals and actions are recorded in `HISTORICAL_CHANGE_LOG.md` and must be consulted by any automation or human before performing secret-sensitive operations.

## Agent conduct & recordkeeping

- All agents (human, CLI, or automated) must read `HISTORICAL_CHANGE_LOG.md` before performing any actions that touch or include sensitive files. Approvals must be explicit, recorded, and discoverable.
- Any overwrite, backup, or inclusion that affects `ops/secrets.env` requires explicit approval recorded as described above. No silent changes are allowed.
- A `secrets_snapshot/` folder is used to store read-only copies of canonical secret files for this repository version. Use `tools/make_secrets_snapshot.py` to create a snapshot and `tools/lock_secrets.sh` to set permissions.
- Agents must follow the `AGENT_POLICIES.md` and use `tools/agent_executor.py` for any approved, actionable commands.
- To list repository changes (the `get_changed_files` tool), agents must request a PIN and approval id in chat and run `python3 tools/require_get_changed_files.py --approval-id <id>` (the script verifies signature using the PIN). Agents must never call git status/get_changed_files directly.

## Git commit safeguards

- A commit-msg hook is provided in `.githooks/commit-msg` that prevents committing changes to `ops/secrets.env` unless the commit message includes an `APPROVAL: <id>` (the approval id must exist in `HISTORICAL_CHANGE_LOG.md`).
- Install hooks locally with: `bash tools/install_git_hooks.sh` (this copies hooks into `.git/hooks/`).
- This protects against accidental or unauthorized secret modifications being committed to the repository.

## Core scripts added

- `tools/build_deployment.py` — builds the deployment, creates manifest and compressed artifact. Has flags to include or exclude `ops/secrets.env`.
- `tools/verify_configs.py` — verifies presence of expected keys and flags in `ops/secrets.env` (read-only).
- `tools/generate_tasks_registry.py` — creates `tools/tasks_registry.json` by scanning launch scripts and tools for docstrings/descriptions.
- `tools/describe_task.py` — CLI helper that prints a human-friendly explanation of a task.
- `tools/task_menu.py` — interactive terminal menu to inspect or execute tasks (execution requires explicit confirmation; `real` mode tasks require `ALLOW_REAL_LAUNCH=1`).

## How to create a deployment (quick)

1. Run: `python3 tools/generate_tasks_registry.py` to generate the task registry.
2. (Optional) Run `python3 tools/verify_configs.py` to validate your `ops/secrets.env`.
3. Run: `python3 tools/build_deployment.py --output build/deployment.tar.gz --include-secrets` to create the compressed artifact.
4. Inspect `build/build_report.json` and `build/release_manifest.json` for verification details.

## One-step installer

For convenience there is a single installer/initializer that performs verification, snapshots, packaging, and smoke tests.

- Run a dry-run first:

  python3 tools/installer.py --dry-run

- When ready, run:

  python3 tools/installer.py

Notes:

- Including secrets requires an approval id and PIN verification: `--include-secrets --approval-id <id>`
- The installer writes a report into `build/installer_reports/` and saves state into `ops/state/installation_state.json`.
- Use `tools/task_menu.py` in the repo to run the `Install & Initialize (full)` interactive option.

## Testing and verification

- Minimal unit tests are provided under `tests/` to validate that build and task registry run and produce expected artifacts.
- The build script prints a summary and produces machine-readable JSON reports for automation.

## FAQ

Q: Will the build remove secrets or modify `ops/secrets.env`?  
A: No. The file is treated as read-only and will only be copied verbatim when `--include-secrets` is used.

Q: I want to ensure no accidental real trades happen during tests.  
A: Tests and the default launch behavior use paper simulation endpoints unless you explicitly set `MODE=real` and `ALLOW_REAL_LAUNCH=1`.

## Support

If you want a custom inclusion/exclusion list for the deployment, open an issue or edit `tools/build_deployment.py` with the patterns you prefer.

---

Generated by automation to standardize a safe, consistent, and verifiable standalone deployment process.
