#!/usr/bin/env python3
"""
AI-Powered Stock & F&O Trading Bot Setup Script
This script helps you set up the trading bot with all necessary configurations.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    print("🚀 AI Trading Bot Setup")
    print("=" * 50)

def check_python_version():
    version = sys.version_info
    print(f"✅ Python version: {sys.version}")
    
    if version.major != 3 or version.minor < 8:
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    if version.minor == 12:
        print("⚠️  Python 3.12 detected - Using compatible package versions")
        return True
    return False

def create_directories():
    print("\n📁 Creating directories...")
    dirs = [
        "logs",
        "models", 
        "data/cache",
        "backtest_results"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")

def install_packages_individually():
    print("\n📦 Installing Python packages individually...")
    
    # Essential packages that should work with Python 3.12
    packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0", 
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "colorlog>=6.7.0",
        "yfinance>=0.2.18",
        "scikit-learn>=1.3.0",
        "python-telegram-bot>=20.0",
        "schedule>=1.2.0",
        "tqdm>=4.65.0",
        "pytz>=2023.3",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "joblib>=1.3.0"
    ]
    
    successful = []
    failed = []
    
    for package in packages:
        try:
            print(f"📦 Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                successful.append(package)
                print(f"✅ {package}")
            else:
                failed.append(package)
                print(f"❌ {package} - {result.stderr[:100]}")
                
        except Exception as e:
            failed.append(package)
            print(f"❌ {package} - {str(e)[:100]}")
    
    print(f"\n📊 Installation Summary:")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print(f"\n⚠️  Failed packages: {', '.join(failed)}")
        print("You can try installing these manually later.")
    
    return len(failed) == 0

def create_env_file():
    print("\n📄 Creating .env file...")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            # Copy from example
            with open(".env.example", "r") as src:
                content = src.read()
            with open(".env", "w") as dst:
                dst.write(content)
            print("✅ Created .env from .env.example")
        else:
            # Create basic .env
            env_content = """# Trading Bot Configuration

# Upstox API
UPSTOX_API_KEY=your_upstox_api_key
UPSTOX_API_SECRET=your_upstox_secret
UPSTOX_ACCESS_TOKEN=your_access_token

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
DATABASE_URL=sqlite:///trading_bot.db

# Trading Parameters
RISK_PERCENTAGE=2.0
MAX_TRADES_PER_DAY=10
MARKET_START_TIME=09:15
MARKET_END_TIME=15:30

# Technical Indicators
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70

# AI Model
MODEL_CONFIDENCE_THRESHOLD=70

# Logging
LOG_LEVEL=INFO
"""
            with open(".env", "w") as f:
                f.write(env_content)
            print("✅ Created basic .env file")
    else:
        print("✅ .env file already exists")

def create_ta_lib_alternative():
    """Create a simple TA-Lib alternative for basic indicators"""
    print("\n🔧 Creating TA-Lib alternative...")
    
    ta_lib_content = '''"""
Simple Technical Analysis Library Alternative
Provides basic indicators without requiring TA-Lib compilation
"""
import pandas as pd
import numpy as np

def RSI(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def MACD(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    exp1 = prices.ewm(span=fast).mean()
    exp2 = prices.ewm(span=slow).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def BBANDS(prices, period=20, std=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    rolling_std = prices.rolling(window=period).std()
    upper = sma + (rolling_std * std)
    lower = sma - (rolling_std * std)
    return upper, sma, lower

def SMA(prices, period):
    """Simple Moving Average"""
    return prices.rolling(window=period).mean()

def EMA(prices, period):
    """Exponential Moving Average"""
    return prices.ewm(span=period).mean()

def SUPERTREND(high, low, close, period=10, multiplier=3):
    """Calculate Supertrend"""
    hl2 = (high + low) / 2
    atr = (high - low).rolling(window=period).mean()
    
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=float)
    
    for i in range(len(close)):
        if i == 0:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
        else:
            if close.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
    
    return supertrend, direction
'''
    
    with open("utils/ta_indicators.py", "w") as f:
        f.write(ta_lib_content)
    print("✅ Created TA indicators alternative")

def main():
    print_header()
    
    # Check Python version
    is_python_312 = check_python_version()
    
    # Create directories
    create_directories()
    
    # Install packages
    success = install_packages_individually()
    
    # Create TA-Lib alternative
    create_ta_lib_alternative()
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
    else:
        print("⚠️  Setup completed with some issues")
    
    print("\n📝 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python test_bot.py")
    print("3. If tests pass, run: python run_bot.py")
    
    if not success:
        print("\n💡 If you encounter issues:")
        print("- Try: pip install --upgrade pip setuptools wheel")
        print("- Or install packages manually: pip install pandas numpy requests")

if __name__ == "__main__":
    main()
