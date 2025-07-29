#!/usr/bin/env python3
"""
🚀 Paper Trading System - Simple Launcher
Guaranteed working launcher for the paper trading system
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher"""
    print("🎯 Paper Trading System - Simple Launcher")
    print("=" * 50)
    
    # Set up paths
    project_root = Path(__file__).parent
    src_path = project_root / 'src'
    
    # Add to Python path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))
    
    try:
        print("🔧 Setting up environment...")
        
        # Test imports
        print("📦 Testing imports...")
        from src.paper_trading.manager import PaperTradingManager
        print("   ✅ Manager imported")
        
        from src.paper_trading.api import app, socketio
        print("   ✅ API imported")
        
        # Initialize system
        print("🎯 Initializing Paper Trading System...")
        manager = PaperTradingManager()
        print("   ✅ Manager initialized")
        
        # Get initial portfolio
        portfolio = manager.get_portfolio()
        balance = portfolio.get('balance', 1000000)
        print(f"   💰 Virtual Balance: ₹{balance:,.2f}")
        
        # Start the Flask server
        print("\n🚀 Starting Paper Trading Server...")
        print("🌐 Dashboard URL: http://localhost:5002")
        print("📱 Features: Stocks & Options Trading")
        print("🔄 Real-time Updates: Enabled")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the server
        socketio.run(app, host='0.0.0.0', port=5002, debug=False)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n🔧 Trying to fix imports...")
        
        # Try alternative import method
        try:
            os.chdir('src/paper_trading')
            import manager
            import api
            print("✅ Alternative import successful")
            
            # Initialize and run
            trading_manager = manager.PaperTradingManager()
            print("✅ Manager initialized via alternative method")
            
            api.socketio.run(api.app, host='0.0.0.0', port=5002, debug=False)
            
        except Exception as e2:
            print(f"❌ Alternative method failed: {e2}")
            print("\n📋 Manual Setup Instructions:")
            print("1. cd src/paper_trading")
            print("2. python api.py")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Please try manual setup:")
        print("1. cd src/paper_trading")
        print("2. python api.py")

if __name__ == "__main__":
    main()
