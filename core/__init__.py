"""
AI Trading Platform - Core Modules
=================================

This package contains the core unified modules for the AI trading platform.

Modules:
    - unified_ai_trading_platform: Main platform orchestrator
    - unified_config: Configuration management
    - unified_database: Database operations
    - unified_live_data: Real-time data feeds
    - unified_notifications: Notification system
    - unified_trading_manager: Trading operations
    - unified_web_dashboard: Web interface

Author: AI Trading Platform
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Trading Platform"

# Core module imports for easier access
from .unified_config import UnifiedConfig
from .unified_database import UnifiedDatabaseManager
from .unified_live_data import UnifiedLiveDataManager
from .unified_notifications import UnifiedNotificationManager
from .unified_trading_manager import UnifiedTradingManager
from .unified_web_dashboard import DashboardManager

__all__ = [
    'UnifiedConfig',
    'UnifiedDatabaseManager', 
    'UnifiedLiveDataManager',
    'UnifiedNotificationManager',
    'UnifiedTradingManager',
    'DashboardManager'
]
