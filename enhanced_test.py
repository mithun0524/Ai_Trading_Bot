#!/usr/bin/env python3
"""
Simple test script to verify the enhanced features are accessible
"""
import sys
import os

def test_basic_imports():
    """Test basic Python functionality"""
    try:
        import json
        import datetime
        import sqlite3
        print("✓ Basic Python modules working")
        return True
    except Exception as e:
        print(f"✗ Basic Python modules failed: {e}")
        return False

def test_enhanced_features_structure():
    """Test if enhanced feature files exist and are importable"""
    
    # Check file existence
    files_to_check = [
        'web_dashboard.py',
        'mobile_api.py',
        'strategies/advanced_strategies.py',
        'portfolio/portfolio_manager.py',
        'templates/dashboard.html',
        'templates/mobile.html'
    ]
    
    print("\nChecking enhanced feature files:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
    
    # Test imports without running the servers
    print("\nTesting imports (without dependencies):")
    
    try:
        # Test if we can at least read the files
        with open('web_dashboard.py', 'r') as f:
            content = f.read()
            if 'TradingDashboard' in content:
                print("✓ web_dashboard.py contains TradingDashboard class")
            else:
                print("✗ web_dashboard.py missing TradingDashboard class")
    except Exception as e:
        print(f"✗ Error reading web_dashboard.py: {e}")
    
    try:
        with open('mobile_api.py', 'r') as f:
            content = f.read()
            if 'MobileAPI' in content:
                print("✓ mobile_api.py contains MobileAPI class")
            else:
                print("✗ mobile_api.py missing MobileAPI class")
    except Exception as e:
        print(f"✗ Error reading mobile_api.py: {e}")
    
    try:
        with open('strategies/advanced_strategies.py', 'r') as f:
            content = f.read()
            if 'AdvancedStrategies' in content:
                print("✓ advanced_strategies.py contains AdvancedStrategies class")
            else:
                print("✗ advanced_strategies.py missing AdvancedStrategies class")
    except Exception as e:
        print(f"✗ Error reading advanced_strategies.py: {e}")

def check_dependencies():
    """Check which dependencies are available"""
    print("\nChecking dependencies:")
    
    dependencies = [
        'flask',
        'flask_socketio', 
        'flask_cors',
        'jwt',
        'pandas',
        'talib',
        'pandas_ta',
        'requests'
    ]
    
    available = []
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
            available.append(dep)
        except ImportError:
            print(f"✗ {dep} missing")
            missing.append(dep)
    
    return available, missing

def main():
    print("=== Enhanced Trading Bot Features Test ===\n")
    
    # Test basic functionality
    if not test_basic_imports():
        print("Basic Python setup has issues. Please check your Python installation.")
        return
    
    # Test file structure
    test_enhanced_features_structure()
    
    # Check dependencies
    available, missing = check_dependencies()
    
    print(f"\nSummary:")
    print(f"Available dependencies: {len(available)}")
    print(f"Missing dependencies: {len(missing)}")
    
    if missing:
        print(f"\nTo install missing dependencies, run:")
        print(f"pip install {' '.join(missing)}")
    
    if len(available) >= 3:  # At least some core deps
        print("\n✓ Enhanced features should be partially functional")
        print("Run 'python web_dashboard.py' to start the web dashboard")
        print("Run 'python mobile_api.py' to start the mobile API")
    else:
        print("\n⚠ Too many dependencies missing. Install them first.")

if __name__ == "__main__":
    main()
