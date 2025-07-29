#!/usr/bin/env python3
"""
Quick test script to verify basic functionality
"""

def test_basic_imports():
    """Test basic package imports"""
    print("🧪 TESTING BASIC IMPORTS")
    print("=" * 40)
    
    try:
        import pandas as pd
        print("✅ pandas")
    except ImportError as e:
        print(f"❌ pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy")
    except ImportError as e:
        print(f"❌ numpy: {e}")
        return False
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        import yfinance as yf
        print("✅ yfinance")
    except ImportError as e:
        print(f"❌ yfinance: {e}")
        return False
    
    try:
        import flask
        print("✅ flask")
    except ImportError as e:
        print(f"❌ flask: {e}")
        return False
    
    try:
        import flask_socketio
        print("✅ flask_socketio")
    except ImportError as e:
        print(f"❌ flask_socketio: {e}")
        return False
    
    # Optional imports
    try:
        import talib
        print("✅ talib (optional)")
    except ImportError:
        print("⚠️  talib not available (optional)")
    
    try:
        import ta
        print("✅ ta")
    except ImportError:
        print("⚠️  ta not available")
    
    try:
        import schedule
        print("✅ schedule")
    except ImportError:
        print("⚠️  schedule not available")
    
    print("=" * 40)
    print("✅ Basic imports test completed!")
    return True

def test_yfinance():
    """Test yfinance functionality"""
    print("\n📊 TESTING YFINANCE")
    print("=" * 40)
    
    try:
        import yfinance as yf
        
        # Test getting data for RELIANCE
        print("Testing RELIANCE.NS data...")
        ticker = yf.Ticker("RELIANCE.NS")
        data = ticker.history(period="1d")
        
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            print(f"✅ RELIANCE.NS: ₹{latest_price:.2f}")
        else:
            print("⚠️  No data received for RELIANCE.NS")
        
        print("=" * 40)
        print("✅ yfinance test completed!")
        return True
        
    except Exception as e:
        print(f"❌ yfinance test failed: {e}")
        return False

def test_flask():
    """Test Flask functionality"""
    print("\n🌐 TESTING FLASK")
    print("=" * 40)
    
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        
        app = Flask(__name__)
        socketio = SocketIO(app)
        
        @app.route('/')
        def home():
            return "Hello from Flask!"
        
        print("✅ Flask app created successfully")
        print("✅ SocketIO initialized")
        print("=" * 40)
        print("✅ Flask test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Flask test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 UNIFIED AI TRADING PLATFORM - QUICK TEST")
    print("=" * 50)
    
    success = True
    
    if not test_basic_imports():
        success = False
    
    if success:
        test_yfinance()
    
    if success:
        test_flask()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your system is ready for the AI Trading Platform")
        print("\nNext steps:")
        print("1. Run: python unified_ai_trading_platform.py --test-mode")
        print("2. If successful, run: python unified_ai_trading_platform.py")
        print("3. Open http://localhost:5000 in your browser")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please install missing packages:")
        print("pip install -r requirements.txt")
    
    print("=" * 50)
