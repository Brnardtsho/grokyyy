# OKX Trade Log

Context file so a new session can resume work. Contains NO credentials, balances or account IDs. Never add any.

## Setup
- Tool: `okx` CLI (`@okx_ai/okx-trade-cli`), OAuth login, site: global, live mode.
- If `okx auth status --json` is not `logged_in`: run `okx auth login --manual --site global` and give the user the URL + code. The `okx-auth` binary may need a manual `curl` download from `static.coinall.ltd/upgradeapp/tools/oauth/linux-x64/` (verify sha256 from `checksum.json`) because the CLI's own downloader ignores the proxy. The environment must allow `www.okx.com` and `static.coinall.ltd`.

## Rules (set with the user, who delegated full discretion)
- Spot only. No leverage, futures, options or bots.
- Max 25% of equity in one new position.
- Every entry has an OCO TP/SL attached on OKX.
- Never withdraw or transfer out.
- Stop and tell the user if equity falls ~15% below the starting equity (start: ~76 USDT).
- Message the user only on: trade closed (P&L), new trade opened, stop-rule hit, or new login needed. No routine reports.

## Supervision
- Scheduled task `OKX trade supervision` (every 4 hours) wakes the session.

## Trades
| # | Opened (UTC) | Pair | Entry | TP | SL | Status | Result |
|---|---|---|---|---|---|---|---|
| 1 | 2026-11-16 17:02 | BTC-USDT | 64,951 | 67,500 | 63,000 | open (OCO live on OKX) | - |

Rationale #1: BTC in a sharp downtrend (80.5k to 65k in two weeks, below EMA20) but 4H RSI ~34 (oversold). Small probe for a short bounce, risk about 0.8% of equity.
