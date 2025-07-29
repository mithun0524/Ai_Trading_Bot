# 🎯 Advanced Paper Trading System

A comprehensive virtual trading platform with real-time market data, options trading, and portfolio management.

## 🚀 Features

### 📊 **Core Trading Features**
- **Virtual Balance**: Start with ₹10,00,000 virtual money
- **Real-time Data**: Live stock prices via Upstox + Yahoo Finance
- **Order Types**: Market, Limit, Stop Loss orders
- **Position Tracking**: Real-time P&L calculation
- **Portfolio Analytics**: Performance metrics and charts

### 📈 **Stock Trading**
- **Equity Trading**: Buy/sell stocks with real market prices
- **Watchlist**: Track favorite stocks with live prices
- **Search**: Find stocks from NIFTY 50 and more
- **Real-time Updates**: Live price updates every 30 seconds

### ⚙️ **Options Trading**
- **Options Chain**: View complete options chain for any stock
- **Strike Prices**: Multiple strike prices around current price
- **Call/Put Options**: Trade both call and put options
- **Expiry Dates**: Multiple expiry dates available
- **Option Pricing**: Realistic option pricing model

### 💼 **Portfolio Management**
- **Live Portfolio**: Real-time portfolio value tracking
- **Position Monitoring**: Track all open positions
- **P&L Analytics**: Detailed profit/loss analysis
- **Trade History**: Complete trade execution history
- **Order Management**: View and manage all orders

### 🔄 **Real-time Features**
- **WebSocket Updates**: Live portfolio updates
- **Price Streaming**: Real-time price updates
- **Instant Execution**: Market orders execute immediately
- **Live Charts**: Real-time market overview charts

## 🛠 Installation & Setup

### 1. **Install Dependencies**
```bash
pip install flask flask-socketio flask-cors pandas numpy
```

### 2. **Test the System**
```bash
python test_paper_trading.py
```

### 3. **Start Paper Trading**
```bash
python paper_trading/start_paper_trading.py
```

### 4. **Access Dashboard**
Open your browser to: `http://localhost:5002`

## 📱 How to Use

### **Getting Started**
1. **Open the Dashboard**: Navigate to `http://localhost:5002`
2. **View Portfolio**: See your ₹10 Lakh virtual balance
3. **Add Stocks**: Search and add stocks to your watchlist
4. **Start Trading**: Place your first buy/sell orders

### **Placing Orders**
1. **Search Symbol**: Type stock name in the search box
2. **Select Stock**: Click on a stock from search results
3. **Enter Quantity**: Specify number of shares
4. **Choose Order Type**: Market or Limit order
5. **Buy/Sell**: Click BUY or SELL button

### **Managing Positions**
- **View Positions**: See all your holdings in the Positions tab
- **Check P&L**: Monitor real-time profit/loss
- **Close Positions**: Click "Close" to sell entire position
- **Track Performance**: View detailed analytics

### **Options Trading**
1. **Go to Options Tab**: Click on the Options tab
2. **Enter Symbol**: Type stock symbol (e.g., RELIANCE)
3. **Load Chain**: Click "Load Chain" to view options
4. **Trade Options**: Click on Call/Put prices to trade

## 🏗 System Architecture

### **Backend Components**
- **PaperTradingManager**: Core trading logic and database operations
- **Flask API**: RESTful endpoints for all trading operations
- **WebSocket Server**: Real-time updates and notifications
- **Data Integration**: Upstox + Yahoo Finance data providers

### **Database Schema**
- **Portfolio**: User balance and overall metrics
- **Positions**: Open trading positions
- **Orders**: Order history and status
- **Trades**: Executed trade details
- **Watchlist**: Favorite stocks tracking

### **Frontend Features**
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live data via WebSocket
- **Interactive Charts**: Market overview and analytics
- **Modern UI**: Clean, professional interface

## 🎮 Trading Examples

### **Example 1: Buy RELIANCE Stock**
```
1. Search "RELIANCE" in symbol search
2. Select RELIANCE from results
3. Enter quantity: 10
4. Select order type: MARKET
5. Click BUY
6. Order executes at current market price
7. Position appears in portfolio
```

### **Example 2: Options Trading**
```
1. Go to Options tab
2. Enter "RELIANCE" in symbol field
3. Click "Load Chain"
4. View call/put options for different strikes
5. Click on option price to trade
6. Execute option order
```

### **Example 3: Portfolio Monitoring**
```
1. View real-time portfolio value
2. Check individual position P&L
3. Monitor day's performance
4. Analyze trade history
5. Track overall returns
```

## 📊 Key Metrics Tracked

### **Portfolio Metrics**
- **Total Value**: Current portfolio worth
- **Available Balance**: Cash available for trading
- **Invested Amount**: Money deployed in positions
- **Total P&L**: Overall profit/loss
- **Day P&L**: Today's performance

### **Position Metrics**
- **Current Price**: Live market price
- **Average Price**: Your buy/sell average
- **Unrealized P&L**: Mark-to-market profit/loss
- **P&L Percentage**: Return percentage
- **Position Size**: Number of shares held

### **Trading Metrics**
- **Order Status**: Pending/Executed/Cancelled
- **Trade Value**: Total transaction value
- **Brokerage**: Trading charges applied
- **Net Value**: Amount after charges

## 🔧 API Endpoints

### **Portfolio**
- `GET /api/portfolio` - Get portfolio summary
- `GET /api/positions` - Get all positions
- `GET /api/orders` - Get order history
- `GET /api/trades` - Get trade history

### **Trading**
- `POST /api/order/place` - Place trading order
- `GET /api/market/quote` - Get stock quote
- `GET /api/market/search` - Search stocks

### **Watchlist**
- `GET /api/watchlist` - Get watchlist
- `POST /api/watchlist/add` - Add to watchlist

### **Options**
- `GET /api/options/chain` - Get options chain

## 🎯 Advanced Features

### **Realistic Trading Simulation**
- **Market Hours**: Respects trading hours
- **Price Impact**: Realistic price movements
- **Brokerage**: Actual brokerage calculation
- **Slippage**: Market impact simulation

### **Risk Management**
- **Position Limits**: Maximum position size controls
- **Stop Loss**: Automatic stop loss orders
- **Margin**: Margin calculation for options
- **Exposure**: Total exposure monitoring

### **Analytics & Reporting**
- **Performance Charts**: Visual performance tracking
- **Trade Analysis**: Detailed trade breakdown
- **Risk Metrics**: Sharpe ratio, drawdown analysis
- **Export Data**: Download trade history

## 🛡 Security Features

### **Data Protection**
- **Local Database**: All data stored locally
- **No Real Money**: Completely virtual trading
- **Safe Testing**: Practice without risk
- **Privacy**: No personal financial data exposed

## 🤝 Integration with Main Bot

### **Signal Integration**
- **AI Signals**: Import signals from main trading bot
- **Auto Trading**: Execute AI-generated signals
- **Backtesting**: Test strategies with historical data
- **Performance**: Compare manual vs automated trading

### **Data Sharing**
- **Market Data**: Shared real-time data feeds
- **Technical Analysis**: Use main bot's indicators
- **Portfolio Sync**: Sync with main portfolio
- **Strategy Testing**: Test strategies before live trading

## 📈 Future Enhancements

### **Planned Features**
- **Futures Trading**: Add futures contracts
- **Crypto Trading**: Virtual cryptocurrency trading
- **Advanced Charts**: Technical analysis charts
- **Social Trading**: Share and follow strategies
- **Mobile App**: Native mobile application

### **Technical Improvements**
- **Performance**: Faster data processing
- **Scalability**: Support multiple users
- **Advanced Orders**: More order types
- **Machine Learning**: AI-powered insights

## 🆘 Troubleshooting

### **Common Issues**
1. **Port 5002 in use**: Change port in `paper_trading_api.py`
2. **Database errors**: Delete `paper_trading.db` to reset
3. **No market data**: Check internet connection
4. **Import errors**: Install missing dependencies

### **Getting Help**
- Check the console logs for detailed error messages
- Run `test_paper_trading.py` to diagnose issues
- Verify all dependencies are installed
- Ensure data providers are accessible

---

## 🎉 Ready to Trade!

Your advanced paper trading system is ready! Start with ₹10 Lakh virtual money and experience realistic trading without any risk.

**Start Trading**: `python paper_trading/start_paper_trading.py`
**Dashboard**: `http://localhost:5002`

Happy Virtual Trading! 🚀📈
