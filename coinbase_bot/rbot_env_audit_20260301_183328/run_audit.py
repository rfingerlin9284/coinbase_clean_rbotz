import os, re, sys, hashlib, pathlib, time
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.expanduser("~"), f"rbot_env_audit_{time.strftime(%Y%m%d_%H%M%S)}")

EXCLUDE_DIRS = {".git","node_modules","venv",".venv","__pycache__","dist","build",".cache",".next",".idea",".vscode"}
ENV_NAME_RE = re.compile(r"^(\.env(\..+)?|.+\.env)$", re.IGNORECASE)

# keys to exclude by user request
EXCLUDE_KEY_RE = re.compile(r"(ALPACA|IBKR)", re.IGNORECASE)

# focus patterns: OANDA, Coinbase Advanced, Telegram, and generic secret-ish keys
FOCUS_KEY_RE = re.compile(
    r"(OANDA|COINBASE|CBA|CB_|TELEGRAM|TOKEN|SECRET|API[_-]?KEY|ACCOUNT|CHAT|PIN|PASS|PRIVATE|JWT)",
    re.IGNORECASE
)

# common env access patterns (python/js/shell)
ENV_ACCESS_RE = re.compile(
    r"(load_dotenv|dotenv|os\.getenv|os\.environ|getenv\(|process\.env|ENV\[|export\s+[A-Za-z_][A-Za-z0-9_]*=)",
    re.IGNORECASE
)

# probable hardcoded secret patterns (extra paranoia)
PROB_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]+PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)

CODE_EXTS = {".py",".js",".ts",".jsx",".tsx",".sh",".bash",".zsh",".ps1",".yaml",".yml",".json",".toml",".ini",".cfg",".md",".txt"}

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "ignore")).hexdigest()

def mask_hint(v: str) -> str:
    n = len(v)
    if n == 0:
        return "<EMPTY>"
    if n <= 4:
        return f"<LEN_{n}_ALL_MASKED>"
    return f"<LAST4_{v[-4:]}>"

def walk_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excludes
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            yield os.path.join(dirpath, fn)

def find_env_files(root: str):
    envs = []
    for p in walk_files(root):
        name = os.path.basename(p)
        if ENV_NAME_RE.match(name):
            envs.append(p)
    return sorted(envs)

def parse_env_file(path: str):
    rows = []
    try:
        st = os.stat(path)
        mtime = int(st.st_mtime)
    except Exception:
        mtime = 0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("export "):
                    line = line[7:].strip()
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                # keep raw value (do not unquote/expand); we want “find & replace” accuracy
                val = val.strip()
                if not key:
                    continue
                rows.append((key, val, path, mtime, len(val), sha256(val)))
    except Exception:
        pass
    return rows

def write_tsv(path: str, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")

def latest_per_key(rows):
    best = {}
    for r in rows:
        key, val, file, mtime, ln, h = r
        # pick newest mtime; tie-break by file path
        if key not in best or (mtime > best[key][3]) or (mtime == best[key][3] and file > best[key][2]):
            best[key] = r
    return [best[k] for k in sorted(best.keys())]

def scan_code(root: str, keys_seen):
    hits_safe = []
    hits_full = []

    # compile a “keys literal” regex for keys we actually saw in envs (so we can catch string references)
    # keep it bounded so it doesn’t explode
    keys_list = sorted({k for k in keys_seen if len(k) >= 3})[:4000]
    key_lit_re = None
    if keys_list:
        # escape and join, but avoid insane-length regex: chunk
        joined = "|".join(re.escape(k) for k in keys_list[:800])  # keep manageable
        key_lit_re = re.compile(rf"({joined})")

    for p in walk_files(root):
        ext = pathlib.Path(p).suffix.lower()
        if ext and ext not in CODE_EXTS:
            continue
        # also scan some key config files even without ext
        base = os.path.basename(p)
        if not ext and base not in {"Dockerfile","Makefile"}:
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    m1 = ENV_ACCESS_RE.search(line)
                    m2 = key_lit_re.search(line) if key_lit_re else None
                    m3 = PROB_SECRET_RE.search(line)
                    if m1 or m2 or m3:
                        tag = []
                        if m1: tag.append("ENV_ACCESS")
                        if m2: tag.append(f"KEY_REF:{m2.group(1)}")
                        if m3: tag.append("PROB_SECRET_PATTERN")
                        hits_safe.append((p, i, ",".join(tag)))
                        hits_full.append((p, i, line.rstrip("\n")))
        except Exception:
            continue

    return hits_safe, hits_full

def redact_text(text: str, values):
    # Replace exact known env values first (best signal)
    for v in values:
        if len(v) < 8:
            continue
        if v in text:
            text = text.replace(v, "<REDACTED_ENV_VALUE>")
    # Then redact obvious token shapes (backup)
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", "sk-<REDACTED>", text)
    text = re.sub(r"-----BEGIN [A-Z ]+PRIVATE KEY-----", "-----BEGIN <REDACTED PRIVATE KEY>-----", text)
    text = re.sub(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "<REDACTED_JWT>", text)
    return text

def main():
    os.makedirs(OUT, exist_ok=True)
    os.chmod(OUT, 0o700)

    env_files = find_env_files(ROOT)

    all_rows = []
    for ef in env_files:
        all_rows.extend(parse_env_file(ef))

    # exclude Alpaca/IBKR keys
    rows_no_ai = [r for r in all_rows if not EXCLUDE_KEY_RE.search(r[0])]

    # safe/redacted variants
    full_rows = [(k,v,f,m,l,h) for (k,v,f,m,l,h) in rows_no_ai]
    red_rows  = [(k,mask_hint(v),f,m,l,h) for (k,v,f,m,l,h) in rows_no_ai]

    latest_rows = latest_per_key(rows_no_ai)
    latest_red  = [(k,mask_hint(v),f,m,l,h) for (k,v,f,m,l,h) in latest_rows]

    focus_rows = [r for r in latest_rows if FOCUS_KEY_RE.search(r[0])]
    focus_red  = [(k,mask_hint(v),f,m,l,h) for (k,v,f,m,l,h) in focus_rows]

    # write outputs
    FULL_TSV       = os.path.join(OUT, "FULL_VALUES.tsv")                # LOCAL ONLY
    RED_TSV        = os.path.join(OUT, "REDACTED_VALUES.tsv")            # safe-ish
    LATEST_TSV     = os.path.join(OUT, "LATEST_PER_KEY.tsv")             # safe-ish
    FOCUS_TSV      = os.path.join(OUT, "LATEST_FOCUS_OANDA_COINBASE.tsv")# safe-ish
    ENV_FILES_TXT  = os.path.join(OUT, "ENV_FILES_FOUND.txt")

    write_tsv(FULL_TSV,   ["key","value","file","mtime_epoch","len","sha256"], full_rows)
    write_tsv(RED_TSV,    ["key","masked_hint","file","mtime_epoch","len","sha256"], red_rows)
    write_tsv(LATEST_TSV, ["key","masked_hint","file","mtime_epoch","len","sha256"], latest_red)
    write_tsv(FOCUS_TSV,  ["key","masked_hint","file","mtime_epoch","len","sha256"], focus_red)

    with open(ENV_FILES_TXT, "w", encoding="utf-8") as f:
        for ef in env_files:
            f.write(ef + "\n")

    os.chmod(FULL_TSV, 0o600)

    # scan code for env usage + key refs + probable hardcoded secrets
    keys_seen = [r[0] for r in rows_no_ai]
    hits_safe, hits_full = scan_code(ROOT, keys_seen)

    HITS_SAFE = os.path.join(OUT, "ENV_CODE_HITS_SAFE.tsv")   # safe-ish (no values)
    HITS_FULL = os.path.join(OUT, "ENV_CODE_HITS_FULL.tsv")   # LOCAL ONLY (line content)
    write_tsv(HITS_SAFE, ["file","line","tag"], hits_safe)
    write_tsv(HITS_FULL, ["file","line","content"], hits_full)
    os.chmod(HITS_FULL, 0o600)

    # Create a locally readable “context” file with best-effort redaction
    values = sorted({r[1] for r in rows_no_ai})  # raw values set
    CONTEXT = os.path.join(OUT, "ENV_CODE_CONTEXT_REDACTED.txt")  # LOCAL ONLY but attempts redaction
    with open(CONTEXT, "w", encoding="utf-8") as out:
        out.write(f"ROOT={ROOT}\nOUT={OUT}\n\n")
        out.write("NOTE: This file tries to redact env values + obvious token patterns, but treat it as LOCAL ONLY.\n\n")
        # group hits by file
        byfile = defaultdict(list)
        for f, ln, content in hits_full:
            byfile[f].append((ln, content))
        for f in sorted(byfile.keys()):
            out.write("\n" + "="*90 + "\n")
            out.write(f"{f}\n")
            out.write("="*90 + "\n")
            # show first N hits with nearby context lines if possible
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as src:
                    lines = src.readlines()
                hit_lines = sorted({ln for (ln,_) in byfile[f]})[:80]
                for ln in hit_lines:
                    start = max(1, ln-3)
                    end   = min(len(lines), ln+3)
                    out.write(f"\n--- around line {ln} ---\n")
                    for j in range(start, end+1):
                        t = lines[j-1].rstrip("\n")
                        t = redact_text(t, values)
                        out.write(f"{j:6d}: {t}\n")
            except Exception:
                # fallback: just list the hit lines (redacted)
                for ln, content in byfile[f][:80]:
                    out.write(f"{ln:6d}: {redact_text(content, values)}\n")

    # Console summary (safe)
    print("DONE.")
    print(f"ROOT scanned: {ROOT}")
    print(f"Output folder: {OUT}")
    print("")
    print("LOCAL ONLY (contains full secret values):")
    print(f"  {FULL_TSV}")
    print("")
    print("SAFE-ish to share here (no values):")
    print(f"  {LATEST_TSV}")
    print(f"  {FOCUS_TSV}")
    print(f"  {HITS_SAFE}")
    print("")
    print("LOCAL ONLY code context (attempted redaction, still treat as local):")
    print(f"  {CONTEXT}")
    print("")
    # show top of focus list
    try:
        with open(FOCUS_TSV, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx > 35: break
                print(line.rstrip("\n"))
    except Exception:
        pass

if __name__ == "__main__":
    main()
