#!/usr/bin/env python3
"""
🎯 Quick Start Paper Trading System
Automated setup and launch script
"""

import os
import sys
import subprocess

def setup_and_start():
    """Setup and start the paper trading system"""
    print("🎯 Paper Trading System - Quick Start")
    print("=" * 50)
    
    try:
        # Step 1: Fix any setup issues
        print("🔧 Step 1: Fixing setup...")
        exec(open('fix_paper_trading.py').read())
        
        # Step 2: Test the system
        print("\n🧪 Step 2: Testing system...")
        test_result = subprocess.run([sys.executable, 'test_paper_trading.py'], 
                                   capture_output=True, text=True)
        
        if test_result.returncode == 0:
            print("✅ System test passed!")
        else:
            print("⚠ System test had some issues, but continuing...")
            print(test_result.stdout)
        
        # Step 3: Start the paper trading system
        print("\n🚀 Step 3: Starting Paper Trading System...")
        print("Dashboard will be available at: http://localhost:5002")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Change to paper_trading directory and start
        os.chdir('paper_trading')
        
        # Import and start the system
        from paper_trading_api import app, socketio
        print("\n✅ Paper Trading System started successfully!")
        print("🌐 Open your browser to: http://localhost:5002")
        print("💰 Virtual Balance: ₹10,00,000")
        print("🔄 Real-time updates enabled")
        
        socketio.run(app, host='0.0.0.0', port=5002, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Paper Trading System stopped by user")
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nTrying to install missing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-socketio', 'flask-cors'])
        print("Please run the script again after installation.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTrying manual approach...")
        
        # Manual fallback
        try:
            print("Attempting to start with manual setup...")
            os.chdir('paper_trading')
            subprocess.run([sys.executable, 'start_paper_trading.py'])
        except Exception as e2:
            print(f"Manual approach also failed: {e2}")
            print("\nPlease check the installation and try:")
            print("1. python fix_paper_trading.py")
            print("2. python test_paper_trading.py") 
            print("3. python paper_trading/start_paper_trading.py")

if __name__ == "__main__":
    setup_and_start()
