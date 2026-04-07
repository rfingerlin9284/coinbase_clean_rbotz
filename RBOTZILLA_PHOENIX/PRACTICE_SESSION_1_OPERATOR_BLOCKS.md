
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

