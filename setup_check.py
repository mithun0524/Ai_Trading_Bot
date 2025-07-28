#!/usr/bin/env python3
"""
Quick setup verification and bot launcher
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking setup requirements...")
    
    issues = []
    
    # Check .env file
    if not Path('.env').exists():
        issues.append("❌ .env file missing")
    else:
        print("✅ .env file found")
    
    # Check Python packages
    try:
        import pandas, numpy, yfinance, telegram
        print("✅ Core packages installed")
    except ImportError as e:
        issues.append(f"❌ Missing package: {e}")
    
    # Check Upstox package
    try:
        import upstox_client
        print("✅ Upstox API v2 client installed")
    except ImportError:
        issues.append("❌ upstox-python-sdk not installed")
    
    return issues

def main():
    print("🚀 AI Trading Bot Setup Checker")
    print("=" * 40)
    
    issues = check_requirements()
    
    if issues:
        print("\n⚠️ Setup Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 Please fix these issues and try again.")
        return False
    
    print("\n🎉 All requirements met!")
    print("\n📝 Next steps:")
    print("1. Run tests: python test_bot.py")
    print("2. Start bot: python run_bot.py")
    
    # Ask if user wants to run tests
    choice = input("\n❓ Run tests now? (y/n): ").lower().strip()
    if choice == 'y':
        print("\n🧪 Running tests...")
        os.system("python test_bot.py")
    
    return True

if __name__ == "__main__":
    main()
