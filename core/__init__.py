"""
🚀 AI Trading Bot - Core Modules
===============================

This package contains the core unified modules for the AI trading platform.

Core Modules:
    - unified_ai_trading_platform: Main platform orchestrator
    - unified_config: Configuration management  
    - unified_database: Database operations
    - unified_live_data: Real-time market data
    - unified_ai_signals: AI signal generation
    - unified_trading_manager: Trading operations
    - unified_web_dashboard: Web interface
    - unified_notifications: Notification system

Version: 2.0.0 (Organized)
Author: AI Trading Platform
"""

__version__ = "2.0.0"
__author__ = "AI Trading Platform"

# Import core components for easier access
try:
    from .unified_config import config
    from .unified_database import db
    from .unified_live_data import live_data_manager  
    from .unified_ai_signals import ai_signal_generator
    from .unified_trading_manager import trading_manager
    from .unified_web_dashboard import dashboard_manager
    from .unified_notifications import notification_manager
    from .unified_ai_trading_platform import UnifiedTradingPlatform
    
    __all__ = [
        'config',
        'db', 
        'live_data_manager',
        'ai_signal_generator',
        'trading_manager',
        'dashboard_manager',
        'notification_manager',
        'UnifiedTradingPlatform'
    ]
    
except ImportError as e:
    # Handle graceful import failures during setup
    pass
