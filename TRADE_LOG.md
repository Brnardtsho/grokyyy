# OKX Trade Log

Context file so a new session can resume work. Contains NO credentials, balances or account IDs. Never add any.

## Setup
- Tool: `okx` CLI (`@okx_ai/okx-trade-cli`), OAuth login, site: global, live mode.
- If `okx auth status --json` is not `logged_in`: run `okx auth login --manual --site global` and give the user the URL + code. The `okx-auth` binary may need a manual `curl` download from `static.coinall.ltd/upgradeapp/tools/oauth/linux-x64/` (verify sha256 from `checksum.json`) because the CLI's own downloader ignores the proxy. The environment must allow `www.okx.com` and `static.coinall.ltd`.

## Rules (set with the user, who delegated full discretion and allowed cautious leverage)
- Spot allowed on any liquid USDT pair (24h volume > 20M USDT; no illiquid or thin small caps, no stablecoin pairs). Perp swaps (USDT-margined) allowed with leverage, under the limits below. No options, no bots.
- Leverage max 3x, ISOLATED margin only, never cross. Perps only on BTC/ETH/SOL/XRP/DOGE/HYPE.
- Only one leveraged position at a time.
- Risk per trade (distance entry to stop x size) <= 1.5% of equity; at most 25% of equity as margin.
- Every entry has a stop-loss on OKX at entry time (attached TP/SL or OCO). No entry without a stop. Never move a stop further away.
- Liquidation price must be at least 2x farther from entry than the stop.
- Never withdraw or transfer out.
- Stop trading and tell the user if equity falls ~15% below the starting equity (start: ~76 USDT). After 3 consecutive losses, pause new entries for 24h.
- Message the user only on: trade closed (P&L), new trade opened, stop-rule hit, or new login needed. No routine reports.

## Supervision
- Scheduled task `OKX trade supervision` (every 4 hours) wakes the session. Helper scripts: `tools/watch.py` (read-only event watcher, run via Monitor) and `tools/scan.py` (read-only scanner + sizing under the rules).

## Trades
| # | Opened (UTC) | Pair | Entry | TP | SL | Status | Result |
|---|---|---|---|---|---|---|---|
| 1 | 2026-11-16 17:02 | BTC-USDT | 64,951 | 67,500 | 63,000 | open (OCO live on OKX) | - |

Rationale #1: BTC in a sharp downtrend (80.5k to 65k in two weeks, below EMA20) but 4H RSI ~34 (oversold). Small probe for a short bounce, risk about 0.8% of equity.
