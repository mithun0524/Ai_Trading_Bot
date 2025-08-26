# Apex AI Trading Platform


![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)

Apex AI Trading Platform is a modern, single-dashboard paper trading solution that combines AI-driven signals, real-time market data, and easy local storage to help traders prototype, backtest, and iterate on strategies quickly and safely. It favors clarity, repeatability, and a minimal install footprint.

Key highlights:
- Sleek black-themed UI optimized for quick situational awareness
- AI signal generator with confidence scores and human-readable reasoning
- Real-time dashboard with WebSocket updates and lightweight REST APIs
- Paper trading engine (orders, fills, P&L) backed by SQLite for portability
- Yahoo Finance (yfinance) for live/historical prices and simple data sourcing
- Optional PWA support for installation to desktop/mobile

---

## Quick links

- Landing page: `/`
- Dashboard: `/app`
- Config: `core/unified_config.py`
- Logs: `trading_platform.log`
- Database: `trading_platform.db`

---

## Why Apex?

You should consider Apex when you want a local, privacy-friendly environment to iterate on trading ideas without risking capital. The platform emphasizes:

- Speed of experimentation — launch locally and start generating signals in minutes
- Explainability — AI signals include confidence and contextual reasoning
- Reproducibility — everything is stored locally in SQLite and EOD reports

---

## Installation (Windows PowerShell)

1. Clone or copy the repo to your machine.
2. Create and activate a Python 3.10+ virtual environment (recommended).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Start the platform:

```powershell
python -u main.py
```

Open http://127.0.0.1:5000 in your browser and click "Open Dashboard".

Run with test data:

```powershell
python -u main.py --test
```

Run with components disabled (debugging):

```powershell
# No dashboard
python -u main.py --no-dashboard

# No scheduler
python -u main.py --no-scheduler
```

---

## Configuration

Edit `core/unified_config.py` to customize:
- Symbols and watchlists
- Risk and sizing parameters
- Indicator hyperparameters and update intervals
- Feature toggles (notifications, PWA, caching behavior)

Best practice: keep a copy of your working config (e.g., `unified_config.local.py`) and do not commit secrets.

---

## API & Socket Surface

REST endpoints (selected):

- `GET /api/portfolio` — current portfolio snapshot
- `GET /api/quotes` — latest quotes for watched symbols
- `GET /api/quote/<symbol>` — latest quote for a symbol
- `GET /api/signals` — last generated signals
- `POST /api/generate_signals` — force signal generation
- `GET /api/orders` — order history
- `POST /api/place_order` — place a paper order
- `GET /api/historical/<symbol>?period=1mo` — historical series

Socket events (client):
- `portfolio_update`, `quotes_update`, `market_update`, `signals_update`, `orders_update`, `trades_update`, `dashboard_update`

---

## Data & Logs

- Runtime log: `trading_platform.log`
- Local DB: `trading_platform.db` (SQLite)
- Daily EOD exports: `eod_report_YYYYMMDD.txt`

The system defaults to local storage and does not ship any cloud integration.

---

## Development & Testing

- Run the app locally and use the `--test` flag to feed deterministic market data.
- Add unit tests under `tests/` (not included by default). Aim for small, fast tests on the signal generator and order engine.

Quick lint/test (if you have pytest/flake8 configured):

```powershell
# install dev deps if you add them
pip install -r requirements-dev.txt; pytest -q
```

---

## Roadmap (short)

1. Add optional broker adapters for live execution behind a feature flag.
2. Improve the AI generator with model versioning and explainability dashboards.
3. Add automated tests and CI for releases.

---

