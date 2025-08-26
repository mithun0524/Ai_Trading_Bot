#!/usr/bin/env python3
"""
🚀 UNIFIED AI TRADING PLATFORM - Main Entry Point
Simple launcher for the complete AI trading system
"""

import sys
import os
import argparse
from pathlib import Path

# Add core directory to Python path
current_dir = Path(__file__).parent
core_dir = current_dir / "core"
sys.path.insert(0, str(core_dir))
sys.path.insert(0, str(current_dir))

def main():
    """Main application launcher"""
    print("🚀 Apex AI Trading Platform")
    print("=" * 50)
    print("🤖 Advanced AI-powered trading system")
    print("📊 Real-time market data & analysis")
    print("💼 Comprehensive portfolio management")
    print("🌐 Web dashboard & mobile support")
    print("📁 Clean organized codebase")
    print("=" * 50)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Apex AI Trading Platform')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--no-dashboard', action='store_true', help='Disable web dashboard')
    parser.add_argument('--no-scheduler', action='store_true', help='Disable task scheduler')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    
    args = parser.parse_args()
    
    # Handle setup mode
    if args.setup:
        try:
            from unified_setup import main as setup_main
            return setup_main()
        except ImportError:
            print("❌ Setup module not found")
            return 1
    
    # Import and run the main trading platform
    try:
        print("📦 Loading trading platform...")
        from unified_ai_trading_platform import UnifiedTradingPlatform, main as platform_main
        
        # Use the platform's main function with arguments
        if args.test:
            sys.argv = ['trading_platform', '--test-mode']
        elif args.no_dashboard:
            sys.argv = ['trading_platform', '--no-dashboard']
        elif args.no_scheduler:
            sys.argv = ['trading_platform', '--no-scheduler']
        else:
            sys.argv = ['trading_platform']
            
        return platform_main()
        
    except ImportError as e:
        print(f"❌ Error importing platform: {e}")
        print("💡 Try running: python main.py --setup")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Platform stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting platform: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
