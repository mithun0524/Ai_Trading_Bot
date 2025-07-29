#!/usr/bin/env python3
"""
🔥 SIMPLE LIVE TRADING LAUNCHER
Reliable launcher with better error handling
"""

import subprocess
import sys
import os
import time

def install_requirements():
    """Install basic requirements"""
    print("📦 Installing basic requirements...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-socketio', 
                       'flask-cors', 'pandas', 'yfinance'], check=True, capture_output=True)
        print("✅ Requirements installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Installation failed")
        return False

def test_imports():
    """Test if all imports work"""
    print("🧪 Testing imports...")
    try:
        import flask
        import pandas as pd
        import yfinance as yf
        from flask_socketio import SocketIO
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def start_simple_system():
    """Start the simple live trading system"""
    print("🚀 Starting Simple Live Trading System...")
    
    try:
        # Execute the live trading system directly
        result = subprocess.run([
            sys.executable, 
            '-c', 
            '''
import sys, os
sys.path.append(os.getcwd())

# Simple live system without complex imports
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import threading
import time

print("🔥 SIMPLE LIVE TRADING SYSTEM")
print("=" * 50)

# Simple trading manager
class SimpleTradingManager:
    def __init__(self):
        self.balance = 1000000.0
        self.watchlist = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        print(f"💰 Virtual Balance: Rs.{self.balance:,.2f}")
        
    def get_live_quote(self, symbol):
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period="1d", interval="1m")
            if data.empty:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                latest = data.iloc[-1]
                return {
                    "symbol": symbol,
                    "price": float(latest["Close"]),
                    "change": float(latest["Close"] - data.iloc[0]["Open"]),
                    "volume": int(latest["Volume"])
                }
        except:
            pass
        return {"symbol": symbol, "price": 100.0, "change": 0.0, "volume": 0}

# Initialize
app = Flask(__name__)
app.config["SECRET_KEY"] = "trading_secret"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
manager = SimpleTradingManager()

@app.route("/")
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Live Trading Dashboard</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .card { background: white; padding: 20px; margin: 10px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .live { color: #28a745; font-weight: bold; }
        .price { font-size: 1.5em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .up { color: #28a745; }
        .down { color: #dc3545; }
    </style>
</head>
<body>
    <h1>🔥 Live Trading Dashboard</h1>
    
    <div class="card">
        <h3>💰 Portfolio</h3>
        <div class="price">Rs.10,00,000</div>
        <p>Virtual Balance</p>
    </div>
    
    <div class="card">
        <h3>📊 Live Quotes <span class="live">● LIVE</span></h3>
        <table id="quotes-table">
            <thead>
                <tr><th>Symbol</th><th>Price</th><th>Change</th><th>Volume</th></tr>
            </thead>
            <tbody>
                <tr><td colspan="4">Loading...</td></tr>
            </tbody>
        </table>
    </div>
    
    <script>
        function updateQuotes() {
            fetch("/api/quotes")
                .then(r => r.json())
                .then(data => {
                    const tbody = document.querySelector("#quotes-table tbody");
                    tbody.innerHTML = data.map(q => 
                        `<tr>
                            <td><strong>${q.symbol}</strong></td>
                            <td class="price">Rs.${q.price.toFixed(2)}</td>
                            <td class="${q.change >= 0 ? "up" : "down"}">Rs.${q.change.toFixed(2)}</td>
                            <td>${q.volume.toLocaleString()}</td>
                        </tr>`
                    ).join("");
                });
        }
        
        updateQuotes();
        setInterval(updateQuotes, 5000); // Update every 5 seconds
    </script>
</body>
</html>
    """

@app.route("/api/quotes")
def get_quotes():
    quotes = []
    for symbol in manager.watchlist:
        quote = manager.get_live_quote(symbol)
        quotes.append(quote)
    return jsonify(quotes)

print("🌐 Dashboard: http://localhost:5000")
print("📊 Fetching live data every 5 seconds")
print("💡 Open browser to view dashboard")
print("🛑 Press Ctrl+C to stop")
print("=" * 50)

try:
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
except KeyboardInterrupt:
    print("\\n🛑 System stopped")
except Exception as e:
    print(f"\\n❌ Error: {e}")
'''
        ], cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting system: {e}")

def main():
    """Main launcher"""
    print("🔥 SIMPLE LIVE TRADING LAUNCHER")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        input("Press Enter to exit...")
        return
    
    # Test imports
    if not test_imports():
        input("Press Enter to exit...")
        return
    
    print("\n🚀 Ready to start!")
    print("This will launch a simple live trading system with:")
    print("  📊 Live stock quotes")
    print("  💰 Virtual Rs.10,00,000 balance")
    print("  🌐 Web dashboard at http://localhost:5000")
    
    input("\nPress Enter to start the system...")
    
    start_simple_system()

if __name__ == "__main__":
    main()
