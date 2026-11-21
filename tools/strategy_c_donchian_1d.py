# STRATEGY C (pre-declared before running, run ONCE, no tuning)
# Daily Donchian trend following, BTC + ETH perps. Classic turtle-style rules.
# Entry: close > highest high of previous 55 days -> LONG ; close < lowest low of previous 55 days -> SHORT
# Exit: close crosses the opposite 20-day channel (long: close < lowest low of prev 20; short: close > highest high of prev 20)
# Initial stop: 2 x ATR(20) from entry (intrabar). Risk 1% of equity per trade. No pyramiding.
# Costs: fee 0.05%/side, slippage 0.02%/side, funding 0.03% of notional per day held (same convention as V1/V2, charged on both sides).
# Fail rule (same as V2): Profit Factor < 1.3 in 2 of 3 windows -> FAILED.
import requests, time
import pandas as pd
import numpy as np

SYMBOLS = ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
TOTAL = 1250
INITIAL_CAPITAL = 1000.0
RISK_PCT = 0.01
FEE = 0.0005
SLIP = 0.0002
FUND_PER_DAY = 0.0003
ENTRY_N, EXIT_N, ATR_N, STOP_K = 55, 20, 20, 2.0

def fetch(inst, total):
    url = "https://www.okx.com/api/v5/market/history-candles"
    rows, after = [], None
    while len(rows) < total:
        p = {"instId": inst, "bar": "1D", "limit": "100"}
        if after: p["after"] = str(after)
        d = requests.get(url, params=p, timeout=15).json().get("data", [])
        if not d: break
        rows.extend(d); after = int(d[-1][0]) - 1; time.sleep(0.2)
    df = pd.DataFrame(rows, columns=["ts","open","high","low","close","vol","vc","vcq","confirm"])
    for c in ["open","high","low","close"]: df[c] = df[c].astype(float)
    df["ts"] = pd.to_datetime(df["ts"].astype(np.int64), unit="ms")
    return df.sort_values("ts").reset_index(drop=True)

def prep(df):
    df["hh_in"] = df["high"].shift(1).rolling(ENTRY_N).max()
    df["ll_in"] = df["low"].shift(1).rolling(ENTRY_N).min()
    df["hh_out"] = df["high"].shift(1).rolling(EXIT_N).max()
    df["ll_out"] = df["low"].shift(1).rolling(EXIT_N).min()
    pc = df["close"].shift(1)
    tr = np.maximum(df["high"]-df["low"], np.maximum((df["high"]-pc).abs(), (df["low"]-pc).abs()))
    df["atr"] = tr.rolling(ATR_N).mean()
    return df

def backtest(df):
    cap = INITIAL_CAPITAL; eq = [cap]; trades = []
    pos = 0; entry = qty = stop = 0.0; ei = 0
    for i in range(ENTRY_N + 1, len(df)):
        r = df.iloc[i]
        if pos != 0:
            exit_px = None
            if pos == 1:
                if r["low"] <= stop: exit_px = stop
                elif r["close"] < r["ll_out"]: exit_px = r["close"]
            else:
                if r["high"] >= stop: exit_px = stop
                elif r["close"] > r["hh_out"]: exit_px = r["close"]
            if exit_px is not None:
                hold = i - ei
                notional = qty * entry
                gross = (exit_px - entry) * qty * pos
                net = gross - notional*FEE*2 - notional*SLIP*2 - notional*FUND_PER_DAY*hold
                cap += net
                trades.append({"date": df.iloc[ei]["ts"], "dir": "LONG" if pos==1 else "SHORT", "net": net, "hold": hold})
                pos = 0
            eq.append(cap); continue
        if pd.isna(r["atr"]) or pd.isna(r["hh_in"]):
            eq.append(cap); continue
        if r["close"] > r["hh_in"]: pos = 1
        elif r["close"] < r["ll_in"]: pos = -1
        if pos != 0:
            entry = r["close"]; ei = i
            dist = STOP_K * r["atr"]
            stop = entry - dist if pos == 1 else entry + dist
            qty = cap * RISK_PCT / dist
        eq.append(cap)
    # close any open position at last close
    if pos != 0:
        r = df.iloc[-1]; hold = len(df)-1-ei; notional = qty*entry
        gross = (r["close"]-entry)*qty*pos
        net = gross - notional*FEE*2 - notional*SLIP*2 - notional*FUND_PER_DAY*hold
        cap += net; trades.append({"date": df.iloc[ei]["ts"], "dir": "LONG" if pos==1 else "SHORT", "net": net, "hold": hold}); eq.append(cap)
    return trades, eq

def report(trades, eq, label):
    if not trades:
        print(f"{label}: No trades"); return None
    t = pd.DataFrame(trades)
    w = t[t.net > 0]; l = t[t.net <= 0]
    pf = w.net.sum()/abs(l.net.sum()) if len(l) else 999
    e = pd.Series(eq); mdd = ((e - e.cummax())/e.cummax()).min()*100
    print(f"\n===== {label} =====")
    print(f"Trades: {len(t)} | Win Rate: {len(w)/len(t)*100:.1f}% | Profit Factor: {pf:.2f} (Need >1.3)")
    print(f"Avg trade: {t.net.mean():.2f} USDT | Total Return: {(eq[-1]-INITIAL_CAPITAL)/INITIAL_CAPITAL*100:.1f}% | Max DD: {mdd:.1f}% | Final: {eq[-1]:.2f}")
    return pf

if __name__ == "__main__":
    for sym in SYMBOLS:
        print(f"\n######## {sym} ########")
        df = prep(fetch(sym, TOTAL))
        print(f"Data {df.ts.min().date()} to {df.ts.max().date()} | {len(df)} daily candles")
        n = len(df); fails = 0
        for w, (s, e) in enumerate([(0, int(n*0.33)), (int(n*0.33), int(n*0.66)), (int(n*0.66), n)]):
            sub = df.iloc[s:e].copy().reset_index(drop=True)
            tr, eq = backtest(sub)
            pf = report(tr, eq, f"Window {w+1} {sub.ts.min().date()} to {sub.ts.max().date()}")
            if pf is None or pf < 1.3: fails += 1
        print(f"\n{sym}: windows with PF<1.3 = {fails}/3 -> {'FAILED' if fails>=2 else 'PASSED'}")
