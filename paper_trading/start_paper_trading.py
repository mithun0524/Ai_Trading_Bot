#!/usr/bin/env python3
"""
🎯 Paper Trading System Launcher
Quick start script for paper trading
"""

import sys
import os

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Change to paper_trading directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🎯 Paper Trading System")
    print("=" * 50)
    print("Starting advanced paper trading system...")
    print("Features:")
    print("✓ Virtual ₹10 Lakh balance")
    print("✓ Real-time stock data")
    print("✓ Options chain trading")
    print("✓ Portfolio tracking")
    print("✓ Order management")
    print("✓ P&L analytics")
    print("=" * 50)
    
    try:
        from paper_trading_api import app, socketio
        print("\n🚀 Paper Trading System starting...")
        print("📊 Dashboard: http://localhost:5002")
        print("🔄 Real-time updates enabled")
        print("💰 Virtual balance: ₹10,00,000")
        print("\nPress Ctrl+C to stop the server")
        
        socketio.run(app, host='0.0.0.0', port=5002, debug=False)
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMissing dependencies. Please install:")
        print("pip install flask flask-socketio flask-cors")
    except Exception as e:
        print(f"\n❌ Error starting paper trading system: {e}")
        print("Check the logs for details.")
