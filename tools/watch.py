#!/usr/bin/env python3
# Read-only watcher: prints one line per notable event. Places NO orders.
import json, subprocess, time, os
env = dict(os.environ, NODE_NO_WARNINGS="1")
def okx(*a):
    try:
        r = subprocess.run(["okx", *a, "--json"], capture_output=True, text=True, timeout=40, env=env)
        return json.loads(r.stdout)
    except Exception:
        return None
def emit(s): print(time.strftime("%H:%M:%S ") + s, flush=True)

base = None; flags = set(); had_algo = None; fails = 0
while True:
    t = okx("market", "ticker", "BTC-USDT")
    if not t:
        fails += 1
        if fails == 5: emit("WARN: OKX unreachable 5x in a row")
        time.sleep(45); continue
    fails = 0
    px = float(t[0]["last"])
    if base is None: base = px
    algos = okx("spot", "algo", "orders")
    if algos is not None:
        live = [a for a in algos if a.get("state") == "live"]
        if had_algo is None: had_algo = bool(live)
        if had_algo and not live:
            emit(f"CLOSED: OCO no longer live (price {px}) - check fills and P&L")
            had_algo = False
        elif live:
            had_algo = True
            for a in live:
                tp, sl = float(a["tpTriggerPx"]), float(a["slTriggerPx"])
                if px >= tp * 0.996 and "tp" not in flags: flags.add("tp"); emit(f"NEAR TP: price {px} vs TP {tp}")
                if px <= sl * 1.004 and "sl" not in flags: flags.add("sl"); emit(f"NEAR SL: price {px} vs SL {sl}")
    if abs(px / base - 1) >= 0.012:
        emit(f"MOVE: BTC {px} ({(px/base-1)*100:+.1f}% vs {base})"); base = px
    r = okx("market", "indicator", "rsi", "BTC-USDT", "--bar", "4H")
    try:
        v = float(r[0]["data"][0]["values"]["14"]) if isinstance(r, list) else None
    except Exception:
        v = None
    st = subprocess.run(["okx", "auth", "status", "--json"], capture_output=True, text=True, env=env).stdout
    if '"logged_in"' not in st and "auth" not in flags:
        flags.add("auth"); emit("AUTH LOST: new login needed")
    time.sleep(45)
