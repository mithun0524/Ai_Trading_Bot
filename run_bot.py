"""
Main entry point for the AI Trading Bot
Run this file to start the trading bot
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the main trading bot
from trading_bot import main

def check_setup():
    """Check if the bot is properly set up"""
    issues = []
    
    # Check if .env file exists
    if not Path('.env').exists():
        issues.append("❌ .env file not found. Copy .env.example to .env and configure your API keys.")
    
    # Check if required directories exist
    required_dirs = ['logs', 'models', 'data/cache']
    for directory in required_dirs:
        if not Path(directory).exists():
            issues.append(f"❌ Directory '{directory}' not found. Run setup.py first.")
    
    # Try importing required packages
    try:
        import pandas
        import numpy
        import talib
        import telegram
        import sklearn
    except ImportError as e:
        issues.append(f"❌ Missing package: {e.name}. Run 'pip install -r requirements.txt'")
    
    return issues

if __name__ == "__main__":
    print("🤖 AI-Powered Trading Bot")
    print("=" * 50)
    
    # Check setup
    setup_issues = check_setup()
    if setup_issues:
        print("Setup issues found:")
        for issue in setup_issues:
            print(issue)
        print("\n🔧 Please run 'python setup.py' first to set up the bot.")
        sys.exit(1)
    
    print("✅ Setup check passed")
    print("🚀 Starting Trading Bot...")
    print("\n📝 Press Ctrl+C to stop the bot")
    print("=" * 50)
    
    try:
        # Run the main bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Trading Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("📝 Check the logs for more details")
    finally:
        print("🔚 Trading Bot shutdown complete")
