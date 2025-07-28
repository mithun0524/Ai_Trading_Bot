# 🚀 AI Trading Bot - Complete Setup & Running Guide

## 🔧 Prerequisites Check
1. **Python 3.12.3** ✅ (Already installed)
2. **All dependencies** ✅ (Already installed)
3. **API credentials** ✅ (Already configured)

## 🎯 How to Run the Trading Bot

### Method 1: Direct Run (Recommended)
```bash
cd "C:\Users\mitun\OneDrive\Desktop\AI AGENT"
python trading_bot.py
```

### Method 2: Using the launcher script
```bash
cd "C:\Users\mitun\OneDrive\Desktop\AI AGENT"
python run_bot.py
```

### Method 3: Using batch file (Windows)
```bash
start_bot.bat
```

## 📱 Telegram Signal Setup

### 1. First Time Setup
Your Telegram bot is already configured with:
- **Bot Token**: `8377747231:AAFFeyFR9ghgzMt5SGUnSRobcpHEWerpihg`
- **Chat ID**: `5344310789`
- **Bot Name**: MyOwnAiTradingbot

### 2. Start Telegram Conversation
1. Open Telegram on your phone/desktop
2. Search for `@MyOwnAiTradingbot`
3. Send `/start` to activate the bot
4. The bot should respond with a welcome message

### 3. Bot Commands
Once running, you can use these Telegram commands:
- `/start` - Initialize bot
- `/status` - Get bot status
- `/watchlist` - See current watchlist
- `/signals` - Get recent signals
- `/performance` - View performance stats

## 🔄 What Happens When You Run the Bot

### 1. Initialization (First 30 seconds)
```
✅ Loading AI model (53.62% accuracy)
✅ Connecting to data sources (Upstox + Yahoo Finance)  
✅ Initializing technical analysis engine
✅ Setting up Telegram notifications
✅ Loading 52-symbol watchlist
✅ Configuring market hours (9:15 AM - 3:30 PM IST)
```

### 2. Market Hours Monitoring (9:15 AM - 3:30 PM)
- **Every 10 minutes**: Scans 5 symbols from watchlist
- **Real-time analysis**: 35+ technical indicators per symbol
- **AI predictions**: Machine learning signal generation
- **Automatic notifications**: Telegram alerts for strong signals

### 3. Signal Generation Process
```
📊 Data Collection → 🔍 Technical Analysis → 🤖 AI Processing → 📱 Telegram Alert
```

## 📈 Types of Signals You'll Receive

### 1. BUY Signals 📈
```
🟢 BUY SIGNAL - RELIANCE
💰 Entry: ₹2,450.50
🎯 Target: ₹2,525.00 (+3.04%)
🛡️ Stop Loss: ₹2,390.25 (-2.46%)
🔥 Confidence: 78%
📊 RSI: 32 (Oversold)
📈 MACD: Bullish crossover
⏰ 10:25 AM
```

### 2. SELL Signals 📉
```
🔴 SELL SIGNAL - TCS
💰 Entry: ₹3,245.75
🎯 Target: ₹3,150.00 (-2.95%)
🛡️ Stop Loss: ₹3,310.50 (+1.99%)
🔥 Confidence: 82%
📊 RSI: 74 (Overbought)
📈 MACD: Bearish divergence
⏰ 11:45 AM
```

### 3. Market Updates 📊
```
📊 MARKET STATUS UPDATE
🕒 Time: 2:30 PM
📈 Nifty: 19,850 (+0.75%)
💼 Signals Today: 8/10
✅ Successful: 6 (75%)
🎯 Next Scan: 2:40 PM
```

## ⚙️ Bot Configuration

### Current Settings:
- **Risk per trade**: 2.0%
- **Max trades per day**: 10
- **Scan frequency**: Every 10 minutes
- **Watchlist**: 52 Nifty stocks
- **AI confidence threshold**: 70%
- **Market hours**: 9:15 AM - 3:30 PM IST

### Customize Settings:
Edit `.env` file to modify:
```
RISK_PERCENTAGE=2.0          # Risk per trade
MAX_TRADES_PER_DAY=10        # Daily signal limit
MODEL_CONFIDENCE_THRESHOLD=70 # AI confidence filter
```

## 🔧 Troubleshooting

### 1. If Bot Doesn't Start:
```bash
# Check dependencies
python test_components.py

# Check logs
tail trading_bot.log
```

### 2. If No Telegram Messages:
1. Verify bot token in `.env`
2. Check your chat ID
3. Send `/start` to bot first
4. Check firewall/internet connection

### 3. If No Signals Generated:
- Bot only generates signals during market hours
- Minimum confidence threshold is 70%
- Daily limit is 10 signals
- Wait for next scan cycle (every 10 minutes)

## 📊 Expected Performance

### Daily Activity:
- **Market scans**: ~36 per day (every 10 minutes)
- **Symbols analyzed**: ~180 per day (5 per scan, rotating)
- **Signals generated**: 3-8 per day (depending on market conditions)
- **Telegram messages**: 10-15 per day (signals + updates)

### Signal Accuracy:
- **AI Model**: 53.62% accuracy (backtested)
- **Technical indicators**: Multiple confirmations required
- **Risk management**: Built-in stop losses and targets

## 🚀 Quick Start Commands

### Start the bot:
```bash
cd "C:\Users\mitun\OneDrive\Desktop\AI AGENT"
python trading_bot.py
```

### Test everything:
```bash
python test_components.py
```

### Train AI model (weekly):
```bash
python train_ai_model.py
```

### Stop the bot:
Press `Ctrl+C` in the terminal

## 📱 Telegram Bot Commands Reference

| Command | Description | Example Response |
|---------|-------------|------------------|
| `/start` | Activate bot | Welcome message + bot status |
| `/status` | Current status | Market open/closed, signals count |
| `/watchlist` | View symbols | List of 52 tracked stocks |
| `/signals` | Recent signals | Last 5 buy/sell signals |
| `/performance` | Daily stats | Win rate, profit/loss summary |
| `/help` | Command list | All available commands |

## 🎯 Success Indicators

You'll know the bot is working when you see:
1. ✅ All component tests pass (100%)
2. 📱 Welcome message from Telegram bot
3. 🔄 Regular "Market scan starting..." logs
4. 📊 Technical analysis completion messages
5. 🚨 Actual buy/sell signal notifications

---

**🎉 Your AI Trading Bot is now ready to generate intelligent trading signals and send them directly to your Telegram!**
