#!/usr/bin/env python3
"""
AI Trading Platform - Main Entry Point
=====================================

This is the main entry point for the unified AI trading platform.
Run this script to start the complete trading system.

Usage:
    python main.py

Requirements:
    - Configured .env file with API credentials
    - Internet connection for market data
    - Telegram bot setup (optional)

Author: AI Trading Platform
Version: 1.0.0
"""

import sys
import os

# Add current directory to Python path for core module imports
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """Main entry point for the AI trading platform"""
    try:
        print("🚀 Starting AI Trading Platform...")
        print("📋 Initializing components...")
        
        # Import the platform module
        from core.unified_ai_trading_platform import UnifiedTradingPlatform
        
        print("✅ Platform imported successfully")
        print("🎯 Creating platform instance...")
        
        # Create and start the platform
        platform = UnifiedTradingPlatform()
        
        print("✅ Platform instance created")
        print("▶️  Starting platform...")
        
        platform.start()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required dependencies are installed.")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Platform stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting platform: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
