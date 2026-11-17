import json, subprocess, os
env=dict(os.environ,NODE_NO_WARNINGS="1")
def candles(inst,bar,n=300):
    r=subprocess.run(["okx","market","candles",inst,"--bar",bar,"--limit",str(n),"--json"],capture_output=True,text=True,env=env)
    d=json.loads(r.stdout); rows=[[float(x) for x in c[:6]] for c in d]
    rows.sort(key=lambda c:c[0]); return rows   # ts,o,h,l,c,v
def ema(v,n):
    k=2/(n+1); e=[v[0]]
    for x in v[1:]: e.append(x*k+e[-1]*(1-k))
    return e
def rsi(c,n=14):
    out=[50]*len(c); g=l=0
    for i in range(1,len(c)):
        d=c[i]-c[i-1]; up=max(d,0); dn=max(-d,0)
        if i<=n: g+=up/n; l+=dn/n
        else: g=(g*(n-1)+up)/n; l=(l*(n-1)+dn)/n
        out[i]=100-100/(1+g/l) if l else 100
    return out
def atr(rows,n=14):
    tr=[rows[0][2]-rows[0][3]]
    for i in range(1,len(rows)):
        h,l,pc=rows[i][2],rows[i][3],rows[i-1][4]; tr.append(max(h-l,abs(h-pc),abs(l-pc)))
    return ema(tr,n)
FEE=0.0010  # 0.05% taker each side (perp), round trip
def sim(rows,signal,rr=1.5,stopk=1.5,maxbars=24):
    a=atr(rows); trades=[]; i=30
    while i<len(rows)-1:
        s=signal(rows,i)
        if s:
            entry=rows[i][4]; stop=stopk*a[i]; tgt=stop*rr
            res=None
            for j in range(i+1,min(i+1+maxbars,len(rows))):
                h,l=rows[j][2],rows[j][3]
                if s==1:
                    if l<=entry-stop: res=-stop; break
                    if h>=entry+tgt: res=tgt; break
                else:
                    if h>=entry+stop: res=-stop; break
                    if l<=entry-tgt: res=tgt; break
            else:
                j=min(i+maxbars,len(rows)-1); res=(rows[j][4]-entry)*s
            trades.append(res/entry-FEE); i=j+1
        else: i+=1
    return trades
def mk(rows):
    c=[r[4] for r in rows]; R=rsi(c); e20=ema(c,20); e50=ema(c,50)
    return c,R,e20,e50
strats={
 "RSI<30 long (mean-rev)": lambda r,i,*_: 1 if S_R[i]<30 else 0,
 "RSI>70 short (mean-rev)": lambda r,i,*_: -1 if S_R[i]>70 else 0,
 "24h breakout long": lambda r,i,*_: 1 if r[i][4]>max(x[2] for x in r[i-24:i]) else 0,
 "24h breakdown short": lambda r,i,*_: -1 if r[i][4]<min(x[3] for x in r[i-24:i]) else 0,
 "trend short (px<EMA20<EMA50, RSI 40-55 pullback)": lambda r,i,*_: -1 if S_C[i]<S_E20[i]<S_E50[i] and 40<S_R[i]<55 else 0,
}
for bar in ("1H","15m"):
    print("== bar",bar)
    tot={k:[] for k in strats}
    for coin in ("BTC","ETH","SOL","XRP","DOGE"):
        rows=candles(f"{coin}-USDT",bar)
        S_C,S_R,S_E20,S_E50=mk(rows)
        for k,f in strats.items(): tot[k]+=sim(rows,f)
    for k,t in tot.items():
        if t: print(f"{k:50s} trades {len(t):3d} | win {sum(x>0 for x in t)/len(t)*100:3.0f}% | avg {sum(t)/len(t)*100:+.3f}% | total {sum(t)*100:+.1f}%")
