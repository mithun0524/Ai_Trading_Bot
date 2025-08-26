# 🚀 Apex AI Trading Platform

A comprehensive AI-powered trading platform that integrates all your trading needs into one unified system.

## 🎯 Features

### 🤖 AI-Powered Trading
- **Advanced Signal Generation**: 5 different AI strategies (Trend Following, Mean Reversion, Momentum, Breakout, Volume Analysis)
- **Multi-indicator Analysis**: RSI, MACD, Bollinger Bands, Stochastic, Williams %R, CCI, ADX
- **Confidence Scoring**: Each signal comes with confidence percentage and detailed reasoning
- **Automated Execution**: Automatic order placement based on high-confidence signals

### 📊 Real-time Market Data
- **Data Source**: Yahoo Finance (enforced)
- **Live Quotes**: Real-time price, volume, and change data
- **Historical Data**: Comprehensive historical data for technical analysis
- **Indian Market Focus**: Pre-configured with NIFTY 50, F&O stocks, and active watchlists

### 💼 Portfolio Management
- **Real-time Tracking**: Live portfolio value and P&L monitoring
- **Position Management**: Automatic position tracking with entry/exit points
- **Risk Management**: Built-in position sizing and stop-loss management
- **Paper Trading**: Safe testing environment with ₹10,00,000 virtual capital

### 🌐 Web Dashboard
- **Single Dashboard**: One clean, minimal black theme at /app
- **Real-time Updates**: Live portfolio, quotes, signals, and orders via WebSocket
- **Responsive**: Works great on desktop and mobile

### 💰 Risk Management
- **Position Sizing**: Automatic calculation based on portfolio percentage and volatility
- **Stop Loss**: Automatic stop-loss placement and monitoring
- **Portfolio Limits**: Maximum position size and daily loss limits
- **Diversification**: Maximum position count and concentration limits

### ⚙️ Automated Operations
- **Scheduled Tasks**: Automatic signal generation, portfolio updates, position monitoring
- **Market Hours Awareness**: Only trades during Indian market hours (9:15 AM - 3:30 PM IST)
- **End-of-Day Reports**: Automatic daily performance and activity reports
- **Data Cleanup**: Automatic cleanup of old data to maintain performance

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Windows/Linux/macOS
- Internet connection for market data

### Quick Setup

1. **Clone or download the platform files**
2. **Run the setup script:**
   ```bash
   python main.py --setup
   ```
3. **Configure your settings:**
   - Edit the `.env` file with your API keys (optional)
   - Modify `core/unified_config.py` for trading parameters
4. **Test the installation:**
   ```bash
   python main.py --test
   ```
5. **Start the platform:**
   ```powershell
   python -u main.py
   ```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install TA-Lib (Windows users may need to download wheel file)
pip install TA-Lib

# Create necessary directories
mkdir logs data reports templates static

# Run the platform
python main.py
```

## 🚀 Quick Start

### 1. Test Mode
```bash
python main.py --test
```
This runs all startup checks without starting the full platform.

### 2. Full Platform
```powershell
python -u main.py
```
Starts the complete platform with:
- AI signal generation
- Real-time data feeds
- Landing page at http://127.0.0.1:5000 and dashboard at http://127.0.0.1:5000/app
- Automated trading (if enabled)

### 3. Disable Components
```bash
# Run without web dashboard
python main.py --no-dashboard

# Run without scheduled tasks
python main.py --no-scheduler
```

## 📊 Usage

### Web Dashboard
1. Open http://127.0.0.1:5000 in your browser (landing)
2. Click "Open Dashboard" to go to /app and view real-time portfolio, signals, and market data
3. Generate signals manually or wait for automatic generation
4. Monitor positions and orders in real-time

### Configuration
Edit `core/unified_config.py` to customize:
- **Watchlists**: Add/remove symbols to track
- **Risk Parameters**: Adjust position sizing and limits
- **Technical Indicators**: Modify RSI, MACD, and other parameters
- **Trading Hours**: Set market timing and schedules

### Environment Variables
Edit `.env` file for:
- **API Keys**: Alpha Vantage, Telegram bot tokens
- **Database**: SQLite database path
- **Logging**: Log levels and file paths
- **Features**: Enable/disable platform features

## 🔧 Architecture

The platform consists of 7 unified modules:

### 1. **core/unified_config.py** - Configuration Management
- Centralized configuration for all components
- Watchlist management (NIFTY 50, F&O, Active symbols)
- Technical indicator parameters
- Risk management settings
- Feature flags

### 2. **core/unified_database.py** - Data Management
- SQLite database with comprehensive schema
- Portfolio, positions, orders, trades tracking
- Signals and live data storage
- Automatic data cleanup and maintenance

### 3. **core/unified_live_data.py** - Market Data
- Yahoo Finance real-time and historical data
- Historical data fetching and caching
- Quote aggregation and normalization
- Async data operations for performance

### 4. **core/unified_ai_signals.py** - AI Signal Generation
- 5 AI strategies with weighted scoring
- Technical analysis with 15+ indicators
- Confidence-based signal filtering
- Automated reasoning and explanation

### 5. **core/unified_trading_manager.py** - Trading Operations
- Paper trading engine with realistic simulation
- Order management (Market, Limit, Stop Loss)
- Position tracking and P&L calculation
- Risk management and validation

### 6. **core/unified_web_dashboard.py** - Web Interface
- Single Flask/Socket.IO dashboard (/app) with landing at /
- Live updates for portfolio, quotes, signals, orders
- PWA assets served from /static

### 7. Platform Orchestration (via `main.py`)
- Orchestrates all components
- Scheduled task management
- Market hours awareness
- Graceful startup/shutdown

## 📈 Trading Strategies

### 1. Trend Following (25% weight)
- Moving average crossovers (SMA 20/50, EMA 12/26)
- ADX trend strength confirmation
- Price position relative to moving averages

### 2. Mean Reversion (20% weight)
- RSI overbought/oversold levels
- Bollinger Bands squeeze and expansion
- Williams %R and CCI extremes

### 3. Momentum (25% weight)
- MACD signal line crossovers
- Stochastic oscillator patterns
- Price momentum indicators
- Intraday momentum analysis

### 4. Breakout (15% weight)
- 20-day high/low breakouts
- Bollinger Bands breakouts
- Volume confirmation
- Support/resistance levels

### 5. Volume Analysis (15% weight)
- Volume vs. average volume
- On-Balance Volume (OBV) trends
- Price-volume divergence
- Volume-weighted signals

## 💡 Key Features

### Intelligent Signal Scoring
Each signal combines all 5 strategies with weighted scoring:
- **BUY Signal**: Weighted score > 20
- **SELL Signal**: Weighted score < -20  
- **HOLD Signal**: Weighted score between -20 and 20
- **Confidence**: Absolute value of weighted score (0-95%)

### Risk Management
- **Position Sizing**: Max 5% of portfolio per position
- **Portfolio Risk**: Max 2% total portfolio risk
- **Daily Limits**: 3% daily loss limit
- **Stop Losses**: Automatic 2% stop loss on all positions
- **Take Profits**: 3% profit targets with 1.5:1 risk-reward

### Market Integration
- **Indian Market Hours**: 9:15 AM - 3:30 PM IST
- **Weekend Awareness**: No trading on weekends
- **Holiday Detection**: Market holiday awareness
- **Pre-configured Symbols**: NIFTY 50, F&O stocks, active symbols

## 📊 Dashboard Features

### Real-time Data
- **Portfolio Summary**: Live value, P&L, positions
- **Market Quotes**: Real-time prices for watchlist symbols  
- **AI Signals**: Latest signals with confidence and reasoning
- **Orders & Trades**: Active orders and completed trades

### Interactive Features
- **Manual Signal Generation**: Generate signals on demand
- **Order Placement**: Place manual orders through the interface
- **Historical Charts**: View price history and indicators
- **Performance Tracking**: Portfolio performance over time

### WebSocket Updates
- **Live Updates**: Real-time data via WebSocket connections
- **Automatic Refresh**: Data updates every 5-30 seconds
- **Connection Status**: Visual connection status indicator
- **Error Handling**: Graceful error handling and reconnection

## 🔒 Security & Safety

### Paper Trading Only
- **No Real Money**: Virtual trading environment only
- **Safe Testing**: Test strategies without financial risk
- **Realistic Simulation**: Includes slippage, commissions, and market conditions

### Data Protection
- **Local Storage**: All data stored locally in SQLite
- **No Account Access**: No broker account integration
- **API Key Security**: Optional API keys stored in environment files

### Risk Controls
- **Position Limits**: Maximum position sizes and counts
- **Loss Limits**: Daily and total loss limits
- **Validation**: Order validation before execution
- **Manual Override**: Manual control over all operations

## 📚 Documentation

### Configuration Files
- **`unified_config.py`**: Main configuration parameters
- **`.env`**: Environment variables and API keys
- **`requirements.txt`**: Python package dependencies

### Log Files
- **`trading_platform.log`**: Main platform logs
- **`eod_report_YYYYMMDD.txt`**: Daily end-of-day reports

### Database
- **`trading_platform.db`**: SQLite database with all data
- **Automatic Backups**: Database backed up during cleanup

## 🚨 Troubleshooting

### Common Issues

#### 1. TA-Lib Installation
**Windows:**
```bash
# Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib‑0.4.xx‑cpxx‑cpxxm‑win_amd64.whl
```

**Linux:**
```bash
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

#### 2. Import Errors
- Ensure all requirements are installed: `pip install -r requirements.txt`
- Check Python version: Must be 3.8 or higher
- Verify virtual environment activation

#### 3. Market Data Issues
- Check internet connection
- Verify symbols are correct (use Indian stock symbols)
- Check Yahoo Finance API status
- Add Alpha Vantage API key for backup

#### 4. Database Errors
- Check file permissions in the directory
- Ensure SQLite is available (built into Python)
- Delete `trading_platform.db` to reset database

#### 5. Web Dashboard Issues
- Check port 5000 is not in use
- Try different port: edit `unified_web_dashboard.py`
- Check firewall settings
- Use `127.0.0.1:5000` instead of `localhost:5000`

### Getting Help
1. Check the log file: `trading_platform.log`
2. Run in test mode: `python main.py --test`
3. Check individual modules work: `python -m core.unified_live_data`
4. Verify configuration: Review `core/unified_config.py` settings

## 🎯 Performance Tips

### Optimization
- **Symbol Limit**: Keep watchlist under 50 symbols for best performance
- **Update Frequency**: Adjust update intervals in configuration
- **Database Cleanup**: Regular cleanup of old data (automatic)
- **Memory Usage**: Monitor memory usage with large datasets

### Best Practices
- **Backtesting**: Test strategies with historical data first
- **Paper Trading**: Always use paper trading mode
- **Risk Management**: Never risk more than you can afford to lose
- **Diversification**: Don't put all capital in one position

## 📞 Support

### Platform Information
- **Version**: 1.0.0
- **Python**: 3.8+ required
- **Database**: SQLite (included)
- **License**: Open source

### Features Status
- ✅ **AI Signals**: Fully implemented with 5 strategies
- ✅ **Live Data**: Yahoo Finance + Alpha Vantage
- ✅ **Paper Trading**: Complete simulation environment
- ✅ **Web Dashboard**: Real-time interface
- ✅ **Risk Management**: Comprehensive controls
- ✅ **Automation**: Scheduled tasks and monitoring

---

## 🎉 Happy Trading!

This unified platform brings together everything you need for AI-powered trading in one integrated system. Start with paper trading, test your strategies, and explore the power of automated AI signals!

**Remember**: This is for educational and paper trading purposes only. Always do your own research and never risk money you cannot afford to lose.

---

*Developed with ❤️ for the trading community*
