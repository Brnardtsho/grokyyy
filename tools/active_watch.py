# Read-only live signal watcher for strategy D (1H Donchian + trend). Prints one line per new signal. No orders.
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__))
import strategy_d_1h as d
COINS = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"]
last_seen = {}
def check(sym):
    df = d.prep(d.fetch(sym, 400)); r = df.iloc[-2]   # last CLOSED 1H candle
    up = r.close > r.e200 and r.e50 > r.e200; dn = r.close < r.e200 and r.e50 < r.e200
    side = "LONG" if (up and r.close > r.hh_in) else "SHORT" if (dn and r.close < r.ll_in) else None
    return side, r
while True:
    for s in COINS:
        try:
            side, r = check(s)
            if side and last_seen.get(s) != r.ts:
                last_seen[s] = r.ts
                print(f"SIGNAL {s} {side} candle {r.ts} close {r.close} atr {r.atr:.4f}", flush=True)
        except Exception as e:
            print("watcher error", s, str(e)[:80], flush=True)
    time.sleep(300)
