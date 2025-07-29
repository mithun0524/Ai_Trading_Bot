# 🚀 Enhanced Trading Bot Setup Guide

## Quick Start (for Windows)

### Step 1: Install Dependencies
Open Command Prompt or PowerShell as Administrator and run:

```bash
pip install flask flask-socketio flask-cors pyjwt pandas-ta requests
```

### Step 2: Test the Installation
Run the test script:
```bash
python enhanced_test.py
```

### Step 3: Start the Enhanced Features

#### Option A: Web Dashboard (Recommended)
```bash
python web_dashboard.py
```
Then open your browser to: http://localhost:5000

#### Option B: Mobile API
```bash
python mobile_api.py
```
The mobile API will run on: http://localhost:5001

#### Option C: Use the Launcher
```bash
python launch_enhanced.py
```

## 📱 Enhanced Features Overview

### 1. Web Dashboard
- **Real-time monitoring** with live charts
- **Trading signals** display
- **Portfolio overview** with performance metrics
- **Mobile-responsive** design
- **WebSocket** updates for live data

### 2. Mobile App Interface
- **Progressive Web App** (PWA) 
- **JWT authentication** for secure access
- **Offline support** with service worker
- **Mobile-optimized** layouts
- **Touch-friendly** controls

### 3. Advanced Trading Strategies
- **Momentum Strategy**: Trend-following with momentum indicators
- **Mean Reversion**: Profit from price reversions to average
- **Breakout Strategy**: Capture significant price movements
- **Scalping**: Quick profits from small price movements
- **Swing Trading**: Medium-term position trading
- **Volume Analysis**: Volume-based trading decisions

### 4. Portfolio Management
- **Risk-based position sizing**
- **Stop loss automation**
- **Sector analysis and diversification**
- **Performance tracking and metrics**

## 🛠 Troubleshooting

### Common Issues:

1. **Import Errors**: If you get "No module named 'talib'":
   - This is normal! The system uses pandas-ta as a fallback
   - All calculations work without TA-Lib

2. **Port Already in Use**:
   - Web dashboard uses port 5000
   - Mobile API uses port 5001
   - Change ports in the respective files if needed

3. **Permission Errors**:
   - Run Command Prompt as Administrator
   - Ensure you have write permissions in the folder

### Manual Dependency Installation:
If pip install fails, try installing one by one:
```bash
pip install flask
pip install flask-socketio
pip install flask-cors
pip install pyjwt
pip install pandas-ta
pip install requests
```

## 📁 File Structure

```
AI AGENT/
├── web_dashboard.py          # Web dashboard server
├── mobile_api.py            # Mobile API server
├── enhanced_test.py         # Test script
├── launch_enhanced.py       # Launcher script
├── strategies/
│   └── advanced_strategies.py  # Advanced trading strategies
├── portfolio/
│   └── portfolio_manager.py    # Portfolio management
├── templates/
│   ├── dashboard.html       # Web dashboard UI
│   └── mobile.html          # Mobile app UI
└── static/
    ├── css/                 # Stylesheets
    ├── js/                  # JavaScript files
    └── manifest.json        # PWA manifest
```

## 🎯 Next Steps

1. **Run the test**: `python enhanced_test.py`
2. **Start web dashboard**: `python web_dashboard.py`
3. **Access via browser**: http://localhost:5000
4. **Check mobile version**: http://localhost:5000/mobile
5. **Install as PWA**: Use browser's "Add to Home Screen"

## 📊 Dashboard Features

- **Live Charts**: Real-time price and indicator charts
- **Trading Signals**: Buy/sell recommendations
- **Portfolio Overview**: Current positions and P&L
- **Risk Metrics**: Drawdown, Sharpe ratio, win rate
- **Strategy Performance**: Individual strategy results

## 📱 Mobile Features

- **Responsive Design**: Works on all screen sizes
- **Touch Navigation**: Swipe and tap controls
- **Offline Mode**: Works without internet
- **Push Notifications**: Trading alerts
- **Biometric Auth**: Fingerprint/Face ID support

---

**Need Help?** Check the error logs or run `python enhanced_test.py` for diagnostics.
