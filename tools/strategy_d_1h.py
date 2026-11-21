# STRATEGY D (pre-declared, run ONCE, no tuning): 1H Donchian breakout with trend filter, BTC/ETH/SOL perps
# Trend: LONG only if close > EMA200 and EMA50 > EMA200; SHORT only if close < EMA200 and EMA50 < EMA200 (1H).
# Entry: close > highest high of previous 24 bars (long) / close < lowest low of previous 24 bars (short), at the signal close.
# Exit: stop 1.5*ATR(14) (intrabar, stop wins ties) OR close crosses the opposite 12-bar channel OR 48 bars max.
# Risk 1% of equity, notional capped at 3x equity. Costs: fee 0.05%/side, slippage 0.02%/side, funding 0.00125% per 1H bar held.
# Fail rule: Profit Factor < 1.3 in 2 of 3 windows (thirds of 3 years) OR max drawdown > 25% in any window.
import sys, time, requests
import pandas as pd, numpy as np

INITIAL = 1000.0; RISK = 0.01; FEE = 0.0005; SLIP = 0.0002; FUND_BAR = 0.0000125
TOTAL = 26300

def fetch(inst, total):
    url = "https://www.okx.com/api/v5/market/history-candles"
    rows, after = [], None
    while len(rows) < total:
        p = {"instId": inst, "bar": "1H", "limit": "100"}
        if after: p["after"] = str(after)
        d = requests.get(url, params=p, timeout=15).json().get("data", [])
        if not d: break
        rows.extend(d); after = int(d[-1][0]) - 1; time.sleep(0.15)
    df = pd.DataFrame(rows, columns=["ts","open","high","low","close","vol","vc","vcq","confirm"])
    for c in ["open","high","low","close"]: df[c] = df[c].astype(float)
    df["ts"] = pd.to_datetime(df["ts"].astype(np.int64), unit="ms")
    return df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)

def prep(df):
    df["e50"] = df.close.ewm(span=50, adjust=False).mean()
    df["e200"] = df.close.ewm(span=200, adjust=False).mean()
    df["hh_in"] = df.high.shift(1).rolling(24).max(); df["ll_in"] = df.low.shift(1).rolling(24).min()
    df["hh_out"] = df.high.shift(1).rolling(12).max(); df["ll_out"] = df.low.shift(1).rolling(12).min()
    pc = df.close.shift(1)
    tr = np.maximum(df.high-df.low, np.maximum((df.high-pc).abs(), (df.low-pc).abs()))
    df["atr"] = tr.rolling(14).mean()
    return df

def backtest(df):
    cap = INITIAL; eq = [cap]; trades = []; pos = 0; entry = qty = stop = 0.0; ei = 0
    for i in range(210, len(df)):
        r = df.iloc[i]
        if pos != 0:
            xp = None
            if pos == 1:
                if r.low <= stop: xp = stop
                elif r.close < r.ll_out: xp = r.close
            else:
                if r.high >= stop: xp = stop
                elif r.close > r.hh_out: xp = r.close
            if xp is None and i - ei >= 48: xp = r.close
            if xp is not None:
                hold = i - ei; notional = qty*entry
                net = (xp-entry)*qty*pos - notional*FEE*2 - notional*SLIP*2 - notional*FUND_BAR*hold
                cap += net; trades.append({"ts": df.iloc[ei].ts, "net": net, "hold": hold}); pos = 0
            eq.append(cap); continue
        if pd.isna(r.atr) or pd.isna(r.hh_in): eq.append(cap); continue
        up = r.close > r.e200 and r.e50 > r.e200; dn = r.close < r.e200 and r.e50 < r.e200
        if up and r.close > r.hh_in: pos = 1
        elif dn and r.close < r.ll_in: pos = -1
        if pos != 0:
            entry = r.close; ei = i; dist = 1.5*r.atr
            stop = entry-dist if pos == 1 else entry+dist
            qty = min(cap*RISK/dist, 3*cap/entry)
        eq.append(cap)
    return trades, eq

def report(sym, label, tr, eq, days):
    if not tr: print(f"{sym} {label}: no trades"); return None, None
    t = pd.DataFrame(tr); w = t[t.net > 0]; l = t[t.net <= 0]
    pf = w.net.sum()/abs(l.net.sum()) if len(l) else 999
    e = pd.Series(eq); mdd = ((e-e.cummax())/e.cummax()).min()*100
    print(f"{sym} {label}: trades {len(t)} ({len(t)/days:.2f}/day) | WR {len(w)/len(t)*100:.1f}% | PF {pf:.2f} | avg {t.net.mean():.2f} | ret {(eq[-1]-INITIAL)/INITIAL*100:.1f}% | maxDD {mdd:.1f}% | final {eq[-1]:.0f}")
    return pf, mdd

if __name__ == "__main__":
    sym = sys.argv[1]
    df = prep(fetch(sym, TOTAL)); n = len(df)
    print(f"{sym}: {df.ts.min().date()} to {df.ts.max().date()} | {n} 1H candles")
    fails = 0
    for w, (s, e) in enumerate([(0, int(n*0.33)), (int(n*0.33), int(n*0.66)), (int(n*0.66), n)]):
        sub = df.iloc[s:e].reset_index(drop=True); days = len(sub)/24
        tr, eq = backtest(sub)
        pf, mdd = report(sym, f"W{w+1} {sub.ts.min().date()}..{sub.ts.max().date()}", tr, eq, days)
        if pf is None or pf < 1.3 or mdd < -25: fails += 1
    print(f"{sym}: failing windows {fails}/3 -> {'FAILED' if fails >= 2 else 'PASSED'}")
