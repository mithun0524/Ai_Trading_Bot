#!/usr/bin/env python3
"""Simple test to verify Python execution"""

print("🚀 Simple Test Starting...")
print("✅ Python is working!")

try:
    import pandas
    print("✅ Pandas imported successfully")
except Exception as e:
    print(f"❌ Pandas import failed: {e}")

try:
    import yfinance
    print("✅ YFinance imported successfully")
except Exception as e:
    print(f"❌ YFinance import failed: {e}")

try:
    from config import Config
    print("✅ Config imported successfully")
except Exception as e:
    print(f"❌ Config import failed: {e}")

print("🎯 Simple test completed!")
