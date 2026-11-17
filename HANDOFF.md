# Handoff: OKX trading agent (for any AI agent taking over)

Read this first, then `TRADE_LOG.md` (rules, open trades, strategy notes). This file has NO credentials. Never ask the user to paste keys, secrets or codes into a chat.

## What this is
The user delegated discretionary trading of their live OKX account (global site, ~76 USDT at start) to an AI agent using the `okx` CLI. All protection (stop-loss / take-profit) lives on OKX servers as algo orders, so positions stay protected even when no agent is running.

## Requirements for the new agent
- A real shell (not a chat-only model) with Node.js, able to reach `www.okx.com` and `static.coinall.ltd`.
- `npm install -g @okx_ai/okx-trade-cli` (CLI name `okx`).
- Official skill docs for the CLI: https://github.com/okx/agent-skills (folder `skills/`, read `okx-cex-trade`, `okx-cex-market`, `okx-cex-auth`).

## Login (OAuth, no secrets typed in chat)
1. `okx auth status --json`. If `logged_in`, you are done.
2. Otherwise: `okx auth login --manual --site global` prints a URL and a code. Give both to the user in plain text; the user opens the URL and enters the code. After they say done, run `okx auth status --json` once.
3. If `okx auth install` fails (downloader ignores the proxy), download the binary with curl from `https://static.coinall.ltd/upgradeapp/tools/oauth/linux-x64/okx-auth`, verify its sha256 against `checksum.json` in the same folder, put it at `~/.okx/bin/okx-auth` and `chmod +x`.
4. Never use an API key with Withdraw permission. Never withdraw or transfer funds out.

## First actions when taking over
1. `okx account balance`, `okx account positions`, `okx spot algo orders`, `okx swap algo orders`, `okx spot fills`.
2. Confirm every open position has a live stop. If one does not, add a stop immediately (or close the position).
3. Run `python3 tools/scan.py <equity>` (read-only scanner) and `tools/watch.py` (read-only event watcher).

## Rules
Follow the rules in `TRADE_LOG.md` exactly (spot allowed; perps only on listed coins; max 3x isolated; risk <= 3% of equity per trade; stop on OKX at entry; never move a stop further away; stop trading and tell the user at ~15% drawdown from ~76 USDT; pause 24h after 3 losses; no withdrawals). Message the user only on: trade closed, trade opened, stop-rule hit, or a login needed. Never promise or guarantee profit; the backtests in `TRADE_LOG.md` cover only one 12-day downtrend.

## If you cannot operate (no shell, no login, no budget)
Do nothing risky. Tell the user to check the OKX app: open positions and their TP/SL orders are visible under pending/algo orders. If any position has no stop, the user should add one or close it in the app.

## Keep the state current
After every trade change: update the Trades table in `TRADE_LOG.md` (no balances, account IDs or credentials; the repo is public) and commit/push to the working branch only.
