#!/usr/bin/env python3
"""
Quick fix script for paper trading system
"""

import os
import sys

def fix_paper_trading_system():
    """Fix common issues with paper trading system setup"""
    print("🔧 Fixing Paper Trading System Setup...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    paper_trading_dir = os.path.join(current_dir, 'paper_trading')
    
    # Create paper_trading directory if it doesn't exist
    if not os.path.exists(paper_trading_dir):
        print("📁 Creating paper_trading directory...")
        os.makedirs(paper_trading_dir)
    
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(paper_trading_dir, 'templates')
    if not os.path.exists(templates_dir):
        print("📁 Creating templates directory...")
        os.makedirs(templates_dir)
    
    # Create __init__.py files to make directories proper Python packages
    init_files = [
        os.path.join(paper_trading_dir, '__init__.py'),
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            print(f"📄 Creating {init_file}...")
            with open(init_file, 'w') as f:
                f.write('# Paper Trading System Package\n')
    
    print("✅ Paper trading system setup fixed!")
    return True

if __name__ == "__main__":
    success = fix_paper_trading_system()
    
    if success:
        print("\n🎯 Now run: python test_paper_trading.py")
        print("Then run: python paper_trading/start_paper_trading.py")
    else:
        print("\n❌ Setup fix failed. Check the errors above.")
