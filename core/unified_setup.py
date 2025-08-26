#!/usr/bin/env python3
"""
🔧 UNIFIED AI TRADING PLATFORM - SETUP SCRIPT
Installation and configuration script for the unified trading platform
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("""
🚀 UNIFIED AI TRADING PLATFORM SETUP
=====================================
🤖 AI-Powered Trading Signals
📊 Real-time Market Data  
💼 Portfolio Management
🌐 Web Dashboard
📈 Paper Trading
💰 Risk Management
🎯 Automated Execution
=====================================
    """)

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    try:
        # Read requirements file
        requirements_file = Path(__file__).parent / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ requirements.txt not found!")
            return False
        
        # Install packages
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All packages installed successfully!")
            return True
        else:
            print("❌ Error installing packages:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def install_talib():
    """Install TA-Lib (requires special handling on Windows)"""
    print("📈 Checking TA-Lib installation...")
    
    try:
        import talib
        print("✅ TA-Lib already installed")
        return True
    except ImportError:
        pass
    
    system = platform.system()
    
    print(f"🔧 Installing TA-Lib for {system}...")
    
    if system == "Windows":
        print("🪟 Windows detected - TA-Lib requires special installation")
        print("📝 Options:")
        print("   1. Try automatic installation (may fail)")
        print("   2. Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
        print("   3. Skip TA-Lib for now (platform will work without it)")
        
        choice = input("Enter choice (1/2/3) [3]: ").strip() or "3"
        
        if choice == "1":
            try:
                cmd = [sys.executable, "-m", "pip", "install", "TA-Lib"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ TA-Lib installed successfully!")
                    return True
                else:
                    print("❌ Automatic TA-Lib installation failed")
                    print("   Try option 2 (manual download) or continue without TA-Lib")
                    return False
            except Exception as e:
                print(f"❌ TA-Lib installation error: {e}")
                return False
        
        elif choice == "2":
            print("📥 Manual installation steps:")
            print("   1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
            print("   2. Download the appropriate .whl file for your Python version")
            print("   3. Install with: pip install <downloaded_file>.whl")
            print("   4. Then re-run this setup")
            return False
        
        else:
            print("⏭️  Skipping TA-Lib installation")
            print("   Note: Some advanced technical indicators may not work")
            return True
    
    elif system == "Linux":
        print("🐧 Linux detected - Installing TA-Lib dependencies...")
        print("📝 You may need to run: sudo apt-get install libta-lib-dev")
        
        try:
            # Try to install TA-Lib
            cmd = [sys.executable, "-m", "pip", "install", "TA-Lib"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ TA-Lib installed successfully!")
                return True
            else:
                print("❌ TA-Lib installation failed")
                print("   Install system dependencies first:")
                print("   sudo apt-get install libta-lib-dev")
                print("   Then run: pip install TA-Lib")
                return False
                
        except Exception as e:
            print(f"❌ TA-Lib installation error: {e}")
            return False
    
    elif system == "Darwin":  # macOS
        print("🍎 macOS detected - Installing TA-Lib...")
        print("📝 You may need to run: brew install ta-lib")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "TA-Lib"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ TA-Lib installed successfully!")
                return True
            else:
                print("❌ TA-Lib installation failed")
                print("   Install with Homebrew first:")
                print("   brew install ta-lib")
                print("   Then run: pip install TA-Lib")
                return False
                
        except Exception as e:
            print(f"❌ TA-Lib installation error: {e}")
            return False
    
    return True  # Continue even if TA-Lib fails

def create_env_file():
    """Create .env file with configuration"""
    print("⚙️  Creating environment configuration...")
    
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping creation")
        return True
    
    env_content = """# UNIFIED AI TRADING PLATFORM CONFIGURATION
# ==========================================

# Alpha Vantage API (for additional data sources)
# Get free API key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Telegram Bot Configuration (optional)
# Create bot with @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Database Configuration
DATABASE_PATH=unified_trading.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=trading_platform.log

# Paper Trading Configuration
INITIAL_CAPITAL=1000000
COMMISSION_RATE=0.001

# Risk Management
MAX_POSITION_SIZE=0.05
MAX_PORTFOLIO_RISK=0.02
DAILY_LOSS_LIMIT=0.03

# AI Signal Configuration
MIN_SIGNAL_CONFIDENCE=60
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70

# Feature Flags
AUTO_TRADING=True
LIVE_DATA=True
PAPER_TRADING=True
WEB_DASHBOARD=True
TELEGRAM_ALERTS=False
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created successfully!")
        print("📝 Please edit .env file to configure your API keys")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "data", 
        "reports",
        "templates",
        "static"
    ]
    
    for dir_name in directories:
        dir_path = Path(__file__).parent / dir_name
        dir_path.mkdir(exist_ok=True)
    
    print("✅ Directories created successfully!")
    return True

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        # Test core imports
        print("   Testing core imports...")
        import pandas as pd
        import numpy as np
        import requests
        print("   ✅ Core packages (pandas, numpy, requests)")
        
        # Test TA-Lib (optional)
        try:
            import talib
            print("   ✅ TA-Lib import successful")
        except ImportError:
            print("   ⚠️  TA-Lib not available (optional - advanced indicators disabled)")
        
        # Test Flask
        try:
            import flask
            import flask_socketio
            print("   ✅ Flask and SocketIO")
        except ImportError:
            print("   ❌ Flask imports failed - web dashboard will not work")
            return False
        
        # Test yfinance
        try:
            import yfinance as yf
            print("   ✅ yfinance (market data)")
        except ImportError:
            print("   ❌ yfinance import failed - market data will not work")
            return False
        
        # Test schedule
        try:
            import schedule
            print("   ✅ schedule (task scheduling)")
        except ImportError:
            print("   ⚠️  schedule import failed - automated tasks disabled")
        
        # Test technical analysis
        try:
            import ta
            print("   ✅ ta (technical analysis)")
        except ImportError:
            print("   ⚠️  ta library not available - some indicators disabled")
        
        # Test plotting
        try:
            import matplotlib.pyplot as plt
            import plotly
            print("   ✅ matplotlib and plotly (charting)")
        except ImportError:
            print("   ⚠️  plotting libraries not fully available")
        
        print("✅ Installation test completed!")
        print("📝 The platform will work with currently installed packages")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def print_next_steps():
    """Print next steps after installation"""
    print("""
🎉 INSTALLATION COMPLETED!
==========================

📝 NEXT STEPS:
1. Edit the .env file to configure your API keys
2. Run the platform in test mode first:
   python unified_ai_trading_platform.py --test-mode

3. Start the full platform:
   python unified_ai_trading_platform.py

4. Access the web dashboard at:
   http://localhost:5000

📊 FEATURES AVAILABLE:
✅ AI Trading Signals
✅ Real-time Market Data
✅ Portfolio Management  
✅ Web Dashboard
✅ Paper Trading
✅ Risk Management
✅ Automated Execution

🔧 CONFIGURATION:
- Edit unified_config.py for trading parameters
- Modify watchlists in the config file
- Adjust risk management settings
- Enable/disable features as needed

📚 DOCUMENTATION:
- Check individual module files for detailed docs
- View logs in trading_platform.log
- Generate reports in the reports/ directory

🚀 HAPPY TRADING!
==========================
    """)

def main():
    """Main setup function"""
    print_banner()
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install requirements
    if success and not install_requirements():
        success = False
    
    # Install TA-Lib (special handling)
    if success:
        install_talib()  # Continue even if this fails
    
    # Create environment file
    if success and not create_env_file():
        success = False
    
    # Create directories
    if success and not create_directories():
        success = False
    
    # Test installation
    if success and not test_installation():
        success = False
    
    if success:
        print_next_steps()
        print("✅ Setup completed successfully!")
        return 0
    else:
        print("❌ Setup failed!")
        print("   Please check the errors above and try again")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
