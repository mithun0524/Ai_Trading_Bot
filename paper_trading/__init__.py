# Paper Trading System Package
"""
Advanced Paper Trading System for Virtual Stock and Options Trading

This package provides:
- Virtual trading with ₹10 Lakh balance
- Real-time stock data integration
- Options chain trading
- Portfolio management
- Order management system
- Real-time P&L tracking
"""

__version__ = "1.0.0"
__author__ = "AI Trading Bot"

from .paper_trading_manager import PaperTradingManager

__all__ = ['PaperTradingManager']
