#!/usr/bin/env python3
"""
Quick test for the fixed enhanced features
"""

print("Testing fixed enhanced features...")

try:
    # Test web dashboard import
    print("Testing web dashboard...")
    from web_dashboard import TradingDashboard
    dashboard = TradingDashboard()
    print("✓ Web dashboard initialization successful!")
    
except Exception as e:
    print(f"✗ Web dashboard error: {e}")

try:
    # Test mobile API import  
    print("Testing mobile API...")
    from mobile_api import MobileAPI
    mobile_api = MobileAPI()
    print("✓ Mobile API initialization successful!")
    
except Exception as e:
    print(f"✗ Mobile API error: {e}")

try:
    # Test advanced strategies
    print("Testing advanced strategies...")
    from strategies.advanced_strategies import AdvancedStrategies
    strategies = AdvancedStrategies()
    print("✓ Advanced strategies initialization successful!")
    
except Exception as e:
    print(f"✗ Advanced strategies error: {e}")

try:
    # Test portfolio manager
    print("Testing portfolio manager...")
    from portfolio.portfolio_manager import AdvancedPortfolioManager
    portfolio = AdvancedPortfolioManager()
    print("✓ Portfolio manager initialization successful!")
    
except Exception as e:
    print(f"✗ Portfolio manager error: {e}")

print("\nTest completed! If you see ✓ for all components, you're ready to go!")
print("\nTo start:")
print("1. Web Dashboard: python web_dashboard.py")
print("2. Mobile API: python mobile_api.py")
print("3. Use the batch file: start_enhanced.bat")
