# OKX Trade Log

Context file so a new session can resume work. Contains NO credentials, balances or account IDs. Never add any.

## Setup
- Tool: `okx` CLI (`@okx_ai/okx-trade-cli`), OAuth login, site: global, live mode.
- If `okx auth status --json` is not `logged_in`: run `okx auth login --manual --site global` and give the user the URL + code. The `okx-auth` binary may need a manual `curl` download from `static.coinall.ltd/upgradeapp/tools/oauth/linux-x64/` (verify sha256 from `checksum.json`) because the CLI's own downloader ignores the proxy. The environment must allow `www.okx.com` and `static.coinall.ltd`.

## Rules (set with the user, who delegated full discretion and allowed cautious leverage)
- Spot allowed on any liquid USDT pair (24h volume > 20M USDT; no illiquid or thin small caps, no stablecoin pairs). Perp swaps (USDT-margined) allowed with leverage, under the limits below. No options, no bots.
- Leverage max 3x, ISOLATED margin only, never cross. Perps only on BTC/ETH/SOL/XRP/DOGE/HYPE.
- Only one leveraged position at a time.
- Risk per trade (distance entry to stop x size) <= 3% of equity (user asked on 2026-11-17 to double the numbers; was 1.5%); at most 40% of equity as margin (was 25%).
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
| 2 | 2026-11-17 11:49 | SOL-USDT-SWAP short 3x isolated, 1.2 SOL | 73.37 | 71.56 | 73.25 (moved from 74.59 after +2%) | CLOSED at TP 71.57 (2026-11-17 15:48 UTC) | +2.07 USDT net of fees (~+2.7% of equity) |
| 3 | 2026-11-17 17:50 | XRP-USDT-SWAP short 3x isolated, 95 XRP (0.95 contracts) | 0.9589 | 0.934 | 0.9757 | open (OCO live on OKX) | - |

Rationale #1: BTC in a sharp downtrend (80.5k to 65k in two weeks, below EMA20) but 4H RSI ~34 (oversold). Small probe for a short bounce, risk about 0.8% of equity.

## Strategy notes
- 2026-11-17 backtest (tools/backtest.py, 300 candles of 1H/15m, 5 coins, 0.1% round-trip fee, ONE downtrend regime of ~12 days, so regime-biased, not proof of edge): RSI<30 long and breakouts lost; short on pullback in downtrend (px < EMA20 < EMA50, RSI 40-55 on 1H, stop 1.5 ATR, target 1.5R) was best on 1H (64 trades, 61% win, +0.38% avg); 15m results weak.
- Entry rule adopted for small-size trials: pullback short in downtrend per above, perp, max 3x, isolated, risk 1.5% equity. Do not open it on a coin where an opposite spot position is open (they cancel). Re-test when the regime changes.

- 2026-11-17 grid-bot simulation (spot grid, 40 USDT, 20 grids, same 12-day downtrend): total PnL -6 to -9 USDT (-15% to -23%), realized only +0.1 to +0.25 USDT. A grid is NOT better than waiting in a falling market; it only works in a sideways range. Re-test if the market turns sideways (low ATR, flat EMA20/50).

Rationale #2: 1H pullback short per strategy notes (px<EMA20<EMA50, RSI1H 51), stop 1.5 x ATR1H, TP 1.5R, risk ~2% of equity, margin ~40% cap.
