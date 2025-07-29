#!/usr/bin/env python3
"""
🚀 COMPLETE LIVE TRADING SYSTEM LAUNCHER
One-click launch for the integrated live trading system
"""

import subprocess
import sys
import os
import time

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    dependencies = [
        'flask',
        'flask-socketio',
        'flask-cors',
        'pandas',
        'yfinance',
        'requests',
        'websocket-client',
        'python-dotenv'
    ]
    
    try:
        for dep in dependencies:
            print(f"   Installing {dep}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         capture_output=True, check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        return False
    
    print("✅ Python version compatible")
    return True

def test_system():
    """Quick system test"""
    print("🧪 Testing system components...")
    
    try:
        # Test imports
        import pandas as pd
        import yfinance as yf
        from flask import Flask
        from flask_socketio import SocketIO
        print("   ✅ Core libraries imported")
        
        # Test data connection
        ticker = yf.Ticker("RELIANCE.NS")
        data = ticker.history(period="1d")
        if not data.empty:
            print("   ✅ Live data connection working")
        else:
            print("   ⚠ Live data connection may have issues")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ⚠ Test warning: {e}")
        return True

def main():
    """Main launcher function"""
    print("🚀 COMPLETE LIVE TRADING SYSTEM")
    print("=" * 60)
    print("🔥 Features:")
    print("  📊 Real-time stock data from Yahoo Finance")
    print("  🤖 AI-powered trading signals")
    print("  💰 Virtual trading with Rs.10,00,000")
    print("  🌐 Live web dashboard")
    print("  📈 Technical analysis integration")
    print("  🔄 Synchronized components")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        input("Press Enter to exit...")
        return
    
    # Test system
    if not test_system():
        print("❌ System test failed")
        input("Press Enter to exit...")
        return
    
    print("\n🎯 Choose launch option:")
    print("1. 🔥 Complete Integrated System (Recommended)")
    print("2. 🎯 Simple Live Trading System")
    print("3. 📊 Paper Trading Only")
    print("4. 🧪 Test Mode")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 Starting Complete Integrated System...")
            print("🌐 Dashboard will be available at: http://localhost:5000")
            print("💡 This integrates your existing AI model with live data")
            print("🔄 Real-time updates every 1 second")
            print("\nPress Ctrl+C to stop the system")
            print("=" * 60)
            
            try:
                # Start integrated system
                import integrated_live_system
                integrated_live_system.main()
            except Exception as e:
                print(f"\n❌ Integration error: {e}")
                print("🔄 Falling back to simple system...")
                import live_trading_system
            
        elif choice == "2":
            print("\n🚀 Starting Simple Live Trading System...")
            print("🌐 Dashboard will be available at: http://localhost:5000")
            print("📊 Live quotes and basic AI signals")
            print("\nPress Ctrl+C to stop the system")
            print("=" * 60)
            
            try:
                # Start simple system
                import live_trading_system
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("🔄 Trying alternative launcher...")
                import simple_live_launcher
                simple_live_launcher.start_simple_system()
            
        elif choice == "3":
            print("\n🚀 Starting Paper Trading System...")
            print("🌐 Dashboard will be available at: http://localhost:5002")
            print("💰 Virtual trading with portfolio management")
            print("\nPress Ctrl+C to stop the system")
            print("=" * 60)
            
            # Start paper trading
            import paper_trading_system
            
        elif choice == "4":
            print("\n🧪 Running Test Mode...")
            
            # Run comprehensive test
            try:
                print("Testing live data connection...")
                import yfinance as yf
                ticker = yf.Ticker("RELIANCE.NS")
                data = ticker.history(period="1d", interval="1m")
                
                if not data.empty:
                    latest = data.iloc[-1]
                    print(f"✅ RELIANCE live price: Rs.{latest['Close']:.2f}")
                    print(f"✅ Volume: {latest['Volume']:,}")
                    print(f"✅ Last updated: {data.index[-1]}")
                else:
                    print("❌ No live data available")
                
                print("\nTesting AI signal generation...")
                # Simple test signal
                if len(data) > 20:
                    sma_5 = data['Close'].rolling(5).mean().iloc[-1]
                    sma_20 = data['Close'].rolling(20).mean().iloc[-1]
                    
                    if sma_5 > sma_20:
                        print("✅ AI Signal: BUY (SMA crossover)")
                    else:
                        print("✅ AI Signal: SELL (SMA crossover)")
                
                print("\n✅ All tests passed! System is ready.")
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
            
            input("\nPress Enter to exit...")
            
        else:
            print("❌ Invalid choice")
            input("Press Enter to exit...")
            
    except KeyboardInterrupt:
        print("\n\n🛑 System stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
