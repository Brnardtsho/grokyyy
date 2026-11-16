#!/usr/bin/env python3
"""Read-only scanner: BTC/ETH/SOL. Prints trend/RSI/BB/funding, a score, and a rule-compliant size for a stop of 1.5 x ATR(4H).
Equity argument: python3 scan.py [equity_usdt]. Places NO orders."""
import json, subprocess, sys, os
env = dict(os.environ, NODE_NO_WARNINGS="1")
def okx(*a):
    try:
        r = subprocess.run(["okx", *a, "--json"], capture_output=True, text=True, timeout=40, env=env)
        return json.loads(r.stdout)
    except Exception: return None
def ind(name, inst, bar, params=None):
    a = [ "market","indicator",name,inst,"--bar",bar] + (["--params",params] if params else [])
    d = okx(*a)
    try:
        tf = d[0]["data"][0]["timeframes"][bar]["indicators"]
        return list(tf.values())[0][0]["values"]
    except Exception: return None
equity = float(sys.argv[1]) if len(sys.argv) > 1 else 76.0
for coin in ("BTC","ETH","SOL","XRP","DOGE","HYPE"):
    inst = f"{coin}-USDT"
    t = okx("market","ticker",inst); px = float(t[0]["last"]) if t else None
    rsi4 = ind("rsi",inst,"4H"); rsi1 = ind("rsi",inst,"1H")
    ema = ind("ema",inst,"1Dutc","20,50"); atr = ind("atr",inst,"4H")
    bb = ind("bb",inst,"4H")
    fr = okx("market","funding-rate",f"{coin}-USDT-SWAP")
    if not (px and rsi4 and ema and atr and bb): print(coin,"data missing"); continue
    r4=float(rsi4["14"]); e20=float(ema["20"]); e50=float(ema["50"]); a=float(atr["14"])
    lo=float(bb["lower"]); hi=float(bb["upper"]); f=float(fr[0]["fundingRate"])*100 if fr else 0
    trend = "DOWN" if px<e20<e50 else "UP" if px>e20>e50 else "MIXED"
    stop = 1.5*a; risk = 0.015*equity
    size_usd = min(risk/(stop/px), equity*0.25*3)   # notional: risk-limited, <=25% equity margin at 3x
    lev = max(1, round(size_usd/(equity*0.25),1))
    # score: + = long bias, - = short bias (mean-reversion at BB extremes only when trend isn't strongly against)
    s = 0
    if px<=lo*1.002 and r4<35: s += 1
    if px>=hi*0.998 and r4>65: s -= 1
    if trend=="UP": s += 1
    if trend=="DOWN": s -= 1
    print(f"{coin}: px {px} | trend {trend} | RSI4H {r4:.0f} | BB4H [{lo:.4g},{hi:.4g}] | ATR4H {a:.4g} | funding {f:.4f}% | score {s:+d} | stop dist {stop:.4g} ({stop/px*100:.1f}%) -> max notional ~{size_usd:.0f} USDT (~{lev}x of 25% equity)")
