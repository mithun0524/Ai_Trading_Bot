# Apex AI Trading Platform

Single-dashboard, Yahoo-only AI paper trading platform with a clean black UI, realtime updates, and local SQLite storage.

## Key features
- Realtime dashboard at /app (landing at /)
- Yahoo Finance only (yfinance) for live/historical data
- AI signal generator with confidence scores and reasoning
- Paper trading engine with orders, trades, and P&L
- SQLite database with daily EOD reports
- PWA manifest + service worker (optional install)

## Quick start (Windows PowerShell)
```powershell
pip install -r requirements.txt
python -u main.py
```
Then open http://127.0.0.1:5000 (landing) and click “Open Dashboard”.

Test mode:
```powershell
python -u main.py --test
```

Disable components:
```powershell
# No dashboard
python -u main.py --no-dashboard
# No scheduler
python -u main.py --no-scheduler
```

## Configure
Edit `core/unified_config.py`:
- symbols and watchlists (NIFTY 50 etc.)
- risk and sizing
- indicator params and update intervals
- feature flags (e.g., notifications)

Logs and data:
- `trading_platform.log` (runtime logs)
- `trading_platform.db` (SQLite)
- `eod_report_YYYYMMDD.txt` (daily reports)

## API and UI
- Landing: `/`
- Dashboard: `/app`
- REST: `/api/portfolio`, `/api/quotes`, `/api/quote/<symbol>`, `/api/signals`, `/api/generate_signals` (POST), `/api/orders`, `/api/place_order` (POST), `/api/watchlist`, `/api/historical/<symbol>?period=1mo`
- Socket events: `portfolio_update`, `quotes_update`, `market_update`, `signals_update`, `orders_update`, `trades_update`, `dashboard_update`, `place_order`, `request_update`

## Notes
- TA-Lib is optional; the app falls back to built‑in indicators if missing.
- Historical sparkline requests are now cached (client + HTTP) to reduce load.
- This is paper trading only—no live broker integration.

## License
MIT
