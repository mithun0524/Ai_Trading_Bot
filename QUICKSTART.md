# Trading Bot Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
# Run the setup script
python setup.py
```

### Step 2: Get Your API Keys

#### Zerodha Kite Connect (Recommended)
1. **Visit**: https://kite.trade/
2. **Login** to your Zerodha account
3. **Go to**: Apps → Kite Connect
4. **Create App**: Fill details and create
5. **Note down**: API Key, API Secret
6. **Generate Access Token**: Use the authentication flow

#### Telegram Bot Setup
1. **Open Telegram** and search for `@BotFather`
2. **Send**: `/newbot`
3. **Choose name**: e.g., "My Trading Bot"
4. **Choose username**: e.g., "mytradingbot123"
5. **Copy the token**: Looks like `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`

#### Get Telegram Chat ID
1. **Send a message** to your bot
2. **Visit**: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. **Find your chat ID** in the response (usually a number like `123456789`)

### Step 3: Configure Environment
1. **Copy** `.env.example` to `.env`
2. **Edit** `.env` file with your keys:

```env
# Zerodha API
KITE_API_KEY=your_kite_api_key_here
KITE_API_SECRET=your_kite_api_secret_here
KITE_ACCESS_TOKEN=your_kite_access_token_here

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=123456789

# Trading Settings (Optional - defaults are good)
RISK_PERCENTAGE=2.0
MAX_TRADES_PER_DAY=10
MODEL_CONFIDENCE_THRESHOLD=70
```

### Step 4: Test the Bot
```bash
# Start the bot
python trading_bot.py
```

You should see:
- ✅ Connection tests
- 🤖 Telegram startup message
- 📊 Market monitoring begins

## 🎯 What Happens Next?

### During Market Hours (9:15 AM - 3:30 PM)
- Bot scans watchlist every 5 minutes
- Generates signals when conditions are met
- Sends alerts to your Telegram

### Sample Signal You'll Receive:
```
🟢 BUY Signal Alert - RELIANCE

🔹 Reason: RSI Oversold (29.3) + MACD Bullish + Supertrend Reversal
📈 Entry: ₹2,485.50
🎯 Target: ₹2,560.00
🛑 SL: ₹2,410.80
🤖 Confidence: 84%
⏰ 11:15 AM - Live Market
```

### Daily Reports (4:00 PM)
```
📊 Trading Bot Performance Report

• Total Signals: 8
• Winning Signals: 6
• Win Rate: 75.0%
• Total P&L: ₹1,250.00
```

## ⚙️ Customization

### Change Watchlist (config.py)
```python
# Add your favorite stocks
NIFTY_50_SYMBOLS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'YOUR_FAVORITE_STOCK'  # Add here
]
```

### Adjust Risk Settings (.env)
```env
# More conservative
RISK_PERCENTAGE=1.0
MAX_TRADES_PER_DAY=5
MODEL_CONFIDENCE_THRESHOLD=80

# More aggressive
RISK_PERCENTAGE=3.0
MAX_TRADES_PER_DAY=15
MODEL_CONFIDENCE_THRESHOLD=60
```

## 🔧 Troubleshooting

### Bot Not Starting?
1. **Check Python version**: Must be 3.8+
2. **Install TA-Lib**: Follow setup instructions
3. **Verify API keys**: Double-check .env file

### No Signals Coming?
1. **Market must be open**: 9:15 AM - 3:30 PM weekdays
2. **Check confidence threshold**: Lower if needed
3. **Verify data connection**: Check logs

### Telegram Not Working?
1. **Test bot token**: Send test message
2. **Check chat ID**: Must be correct
3. **Add bot to group**: If using group chat

## 📊 Understanding Signals

### Signal Types
- **🟢 BUY**: Bullish indicators align
- **🔴 SELL**: Bearish indicators align  
- **🟡 NEUTRAL**: Mixed signals (not sent)

### Confidence Levels
- **80-100%**: Very strong signal
- **70-79%**: Good signal
- **60-69%**: Moderate signal
- **<60%**: Weak (filtered out)

### Reasons You'll See
- **RSI Oversold/Overbought**
- **MACD Bullish/Bearish Crossover**
- **Supertrend Reversal**
- **Bollinger Band Squeeze**
- **Moving Average Crossover**
- **Candlestick Patterns**

## 💡 Pro Tips

### 1. Start Conservative
- Begin with default settings
- Monitor for 1-2 weeks
- Adjust based on performance

### 2. Paper Trade First
- Test signals without real money
- Track performance manually
- Build confidence in the system

### 3. Don't Overtrade
- Stick to daily limits
- Quality over quantity
- Respect stop losses

### 4. Monitor Performance
- Check daily reports
- Analyze losing trades
- Adjust parameters gradually

## 🚨 Important Notes

### ⚠️ Risk Disclaimer
- **This is NOT financial advice**
- **Always do your own research**
- **Start with small amounts**
- **Never risk more than you can afford to lose**

### 🔄 Bot Limitations
- **Requires internet connection**
- **Depends on data provider uptime**
- **Market volatility can affect accuracy**
- **Past performance ≠ future results**

### 📱 Best Practices
1. **Keep bot running** during market hours
2. **Monitor Telegram regularly**
3. **Review performance weekly**
4. **Update API tokens** when needed
5. **Backup database** periodically

## 🎉 You're Ready!

Your AI trading bot is now set up and ready to help you catch market opportunities. Remember to trade responsibly and always combine AI insights with your own analysis.

**Happy Trading! 📈🚀**

---

*Need help? Check the main README.md for detailed documentation.*
