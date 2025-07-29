"""
🎯 Paper Trading Package
Advanced virtual trading system for stocks and options
"""

from .manager import PaperTradingManager

try:
    from .api import app, socketio
except ImportError:
    app = None
    socketio = None

__version__ = "2.0.0"
__author__ = "AI Trading Bot"

__all__ = [
    'PaperTradingManager',
    'app',
    'socketio'
]
