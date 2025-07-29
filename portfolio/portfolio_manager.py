#!/usr/bin/env python3
"""
💼 Advanced Portfolio Manager
Risk management, position sizing, and portfolio optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from config import Config
from utils.logger import logger

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AGGRESSIVE = "aggressive"

@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    position_type: str  # LONG, SHORT
    entry_date: datetime
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None

@dataclass
class RiskMetrics:
    portfolio_value: float
    total_exposure: float
    max_position_size: float
    var_95: float  # Value at Risk 95%
    sharpe_ratio: float
    max_drawdown: float
    beta: float

class AdvancedPortfolioManager:
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.cash_balance = initial_capital
        self.risk_level = RiskLevel.MEDIUM
        self.max_portfolio_risk = 0.02  # 2% max risk per trade
        self.max_position_size = 0.1    # 10% max position size
        
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float, confidence: float) -> int:
        """Calculate optimal position size based on risk management"""
        try:
            # Risk amount based on portfolio and confidence
            risk_multiplier = self._get_risk_multiplier(confidence)
            risk_amount = self.current_capital * self.max_portfolio_risk * risk_multiplier
            
            # Calculate position size based on stop loss distance
            if stop_loss and entry_price != stop_loss:
                price_risk = abs(entry_price - stop_loss)
                position_value = risk_amount / (price_risk / entry_price)
                
                # Ensure position doesn't exceed max position size
                max_position_value = self.current_capital * self.max_position_size
                position_value = min(position_value, max_position_value)
                
                # Ensure we have enough cash
                position_value = min(position_value, self.cash_balance * 0.95)
                
                quantity = int(position_value / entry_price)
                return max(1, quantity)  # At least 1 share
            else:
                # Default position size if no stop loss
                default_position_value = self.current_capital * 0.05  # 5% default
                return max(1, int(default_position_value / entry_price))
                
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 1
    
    def _get_risk_multiplier(self, confidence: float) -> float:
        """Get risk multiplier based on signal confidence"""
        if confidence >= 85:
            return 1.5  # Increase risk for high confidence
        elif confidence >= 75:
            return 1.2
        elif confidence >= 65:
            return 1.0
        else:
            return 0.7  # Reduce risk for low confidence
    
    def add_position(self, symbol: str, signal_type: str, entry_price: float,
                    confidence: float, stop_loss: Optional[float] = None,
                    target_price: Optional[float] = None) -> bool:
        """Add a new position to the portfolio"""
        try:
            # Check if we already have a position in this symbol
            if symbol in self.positions:
                logger.warning(f"Already have position in {symbol}")
                return False
            
            # Calculate position size
            quantity = self.calculate_position_size(symbol, entry_price, stop_loss, confidence)
            position_value = quantity * entry_price
            
            # Check if we have enough cash
            if position_value > self.cash_balance:
                logger.warning(f"Insufficient cash for {symbol} position: {position_value} > {self.cash_balance}")
                return False
            
            # Create position
            position = Position(
                symbol=symbol,
                quantity=quantity if signal_type == "BUY" else -quantity,
                entry_price=entry_price,
                current_price=entry_price,
                position_type="LONG" if signal_type == "BUY" else "SHORT",
                entry_date=datetime.now(),
                stop_loss=stop_loss,
                target_price=target_price
            )
            
            # Update portfolio
            self.positions[symbol] = position
            self.cash_balance -= position_value
            
            logger.info(f"Added position: {symbol} {signal_type} {quantity} @ {entry_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding position for {symbol}: {e}")
            return False
    
    def update_position_price(self, symbol: str, current_price: float):
        """Update current price for a position"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = current_price
            
            # Calculate unrealized P&L
            if position.position_type == "LONG":
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            else:  # SHORT
                position.unrealized_pnl = (position.entry_price - current_price) * abs(position.quantity)
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "manual") -> Optional[float]:
        """Close a position and realize P&L"""
        try:
            if symbol not in self.positions:
                return None
            
            position = self.positions[symbol]
            
            # Calculate realized P&L
            if position.position_type == "LONG":
                realized_pnl = (exit_price - position.entry_price) * position.quantity
            else:  # SHORT
                realized_pnl = (position.entry_price - exit_price) * abs(position.quantity)
            
            # Update cash balance
            position_value = abs(position.quantity) * exit_price
            self.cash_balance += position_value + realized_pnl
            
            # Update capital
            self.current_capital += realized_pnl
            
            # Log the trade
            logger.info(f"Closed position: {symbol} {position.position_type} P&L: {realized_pnl:.2f} Reason: {reason}")
            
            # Remove position
            del self.positions[symbol]
            
            return realized_pnl
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return None
    
    def check_stop_losses(self, market_data: Dict[str, float]) -> List[str]:
        """Check and execute stop losses"""
        closed_positions = []
        
        for symbol, position in list(self.positions.items()):
            if symbol not in market_data or not position.stop_loss:
                continue
            
            current_price = market_data[symbol]
            self.update_position_price(symbol, current_price)
            
            # Check stop loss condition
            should_close = False
            if position.position_type == "LONG" and current_price <= position.stop_loss:
                should_close = True
            elif position.position_type == "SHORT" and current_price >= position.stop_loss:
                should_close = True
            
            if should_close:
                self.close_position(symbol, current_price, "stop_loss")
                closed_positions.append(symbol)
        
        return closed_positions
    
    def check_targets(self, market_data: Dict[str, float]) -> List[str]:
        """Check and execute target prices"""
        closed_positions = []
        
        for symbol, position in list(self.positions.items()):
            if symbol not in market_data or not position.target_price:
                continue
            
            current_price = market_data[symbol]
            self.update_position_price(symbol, current_price)
            
            # Check target condition
            should_close = False
            if position.position_type == "LONG" and current_price >= position.target_price:
                should_close = True
            elif position.position_type == "SHORT" and current_price <= position.target_price:
                should_close = True
            
            if should_close:
                self.close_position(symbol, current_price, "target_reached")
                closed_positions.append(symbol)
        
        return closed_positions
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_position_value = sum(abs(pos.quantity) * pos.current_price for pos in self.positions.values())
            portfolio_value = self.cash_balance + total_position_value
            
            # Performance metrics
            total_return = portfolio_value - self.initial_capital
            return_percentage = (total_return / self.initial_capital) * 100
            
            # Risk metrics
            risk_metrics = self.calculate_risk_metrics()
            
            return {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'cash_balance': round(self.cash_balance, 2),
                'portfolio_value': round(portfolio_value, 2),
                'total_positions': len(self.positions),
                'total_unrealized_pnl': round(total_unrealized_pnl, 2),
                'total_return': round(total_return, 2),
                'return_percentage': round(return_percentage, 2),
                'positions': self._get_positions_summary(),
                'risk_metrics': risk_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}
    
    def _get_positions_summary(self) -> List[Dict]:
        """Get summary of all positions"""
        positions_summary = []
        
        for symbol, position in self.positions.items():
            position_value = abs(position.quantity) * position.current_price
            unrealized_pnl_percent = (position.unrealized_pnl / (abs(position.quantity) * position.entry_price)) * 100
            
            positions_summary.append({
                'symbol': symbol,
                'type': position.position_type,
                'quantity': position.quantity,
                'entry_price': round(position.entry_price, 2),
                'current_price': round(position.current_price, 2),
                'position_value': round(position_value, 2),
                'unrealized_pnl': round(position.unrealized_pnl, 2),
                'unrealized_pnl_percent': round(unrealized_pnl_percent, 2),
                'entry_date': position.entry_date.strftime('%Y-%m-%d %H:%M:%S'),
                'stop_loss': position.stop_loss,
                'target_price': position.target_price
            })
        
        return positions_summary
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        try:
            portfolio_value = self.cash_balance + sum(abs(pos.quantity) * pos.current_price for pos in self.positions.values())
            total_exposure = sum(abs(pos.quantity) * pos.current_price for pos in self.positions.values())
            
            # Calculate max position size
            max_position_value = 0
            if self.positions:
                max_position_value = max(abs(pos.quantity) * pos.current_price for pos in self.positions.values())
            
            # Simplified risk calculations (in production, use historical data)
            var_95 = portfolio_value * 0.05  # Simple 5% VaR
            sharpe_ratio = 1.2  # Mock value
            max_drawdown = 0.08  # Mock value
            beta = 1.1  # Mock value
            
            return RiskMetrics(
                portfolio_value=portfolio_value,
                total_exposure=total_exposure,
                max_position_size=max_position_value,
                var_95=var_95,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                beta=beta
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0)
    
    def optimize_portfolio(self) -> Dict:
        """Suggest portfolio optimizations"""
        suggestions = []
        
        try:
            summary = self.get_portfolio_summary()
            
            # Check diversification
            if len(self.positions) < 3:
                suggestions.append("Consider diversifying across more symbols")
            
            # Check position sizes
            for pos_summary in summary['positions']:
                if pos_summary['position_value'] > self.current_capital * 0.15:
                    suggestions.append(f"Position in {pos_summary['symbol']} is too large (>15% of portfolio)")
            
            # Check cash utilization
            cash_percentage = (self.cash_balance / summary['portfolio_value']) * 100
            if cash_percentage > 50:
                suggestions.append("High cash balance - consider investing more capital")
            elif cash_percentage < 10:
                suggestions.append("Low cash balance - consider reducing positions for liquidity")
            
            # Risk level suggestions
            risk_metrics = summary['risk_metrics']
            if risk_metrics.total_exposure > summary['portfolio_value'] * 0.8:
                suggestions.append("High portfolio exposure - consider reducing position sizes")
            
            return {
                'suggestions': suggestions,
                'current_risk_level': self.risk_level.value,
                'diversification_score': min(100, len(self.positions) * 20),
                'cash_utilization': round(100 - cash_percentage, 2)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")
            return {'suggestions': [], 'current_risk_level': 'unknown', 'diversification_score': 0, 'cash_utilization': 0}
    
    def set_risk_level(self, risk_level: RiskLevel):
        """Set portfolio risk level and adjust parameters"""
        self.risk_level = risk_level
        
        if risk_level == RiskLevel.LOW:
            self.max_portfolio_risk = 0.01  # 1%
            self.max_position_size = 0.05   # 5%
        elif risk_level == RiskLevel.MEDIUM:
            self.max_portfolio_risk = 0.02  # 2%
            self.max_position_size = 0.1    # 10%
        elif risk_level == RiskLevel.HIGH:
            self.max_portfolio_risk = 0.03  # 3%
            self.max_position_size = 0.15   # 15%
        elif risk_level == RiskLevel.AGGRESSIVE:
            self.max_portfolio_risk = 0.05  # 5%
            self.max_position_size = 0.2    # 20%
        
        logger.info(f"Risk level set to {risk_level.value}")
    
    def get_performance_analytics(self, days: int = 30) -> Dict:
        """Get detailed performance analytics"""
        try:
            # In production, this would query historical trades from database
            # For now, return mock analytics
            
            return {
                'period_days': days,
                'total_trades': 25,
                'winning_trades': 16,
                'losing_trades': 9,
                'win_rate': 64.0,
                'avg_win': 2.3,
                'avg_loss': -1.8,
                'profit_factor': 2.04,
                'max_consecutive_wins': 5,
                'max_consecutive_losses': 3,
                'average_holding_period': 4.2,
                'best_trade': 8.5,
                'worst_trade': -4.2,
                'recovery_factor': 1.8,
                'calmar_ratio': 0.85
            }
            
        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {}

class RiskManager:
    """Advanced risk management utilities"""
    
    def __init__(self, portfolio_manager: AdvancedPortfolioManager):
        self.portfolio_manager = portfolio_manager
        
    def calculate_correlation_risk(self, symbols: List[str]) -> Dict[str, float]:
        """Calculate correlation risk between positions"""
        # In production, this would calculate actual correlations
        # For now, return mock correlation data
        
        correlations = {}
        for symbol in symbols:
            # Mock correlations (in practice, use historical price data)
            if 'BANK' in symbol or symbol in ['HDFCBANK', 'ICICIBANK', 'SBIN']:
                correlations[symbol] = 0.7  # High correlation within banking sector
            elif symbol in ['RELIANCE', 'ONGC']:
                correlations[symbol] = 0.6  # Energy sector correlation
            else:
                correlations[symbol] = 0.3  # Lower correlation
        
        return correlations
    
    def calculate_sector_exposure(self) -> Dict[str, float]:
        """Calculate exposure by sector"""
        sector_exposure = {}
        
        # Mock sector classification
        sector_mapping = {
            'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking',
            'RELIANCE': 'Energy', 'ONGC': 'Energy',
            'TCS': 'IT', 'INFY': 'IT',
            'ITC': 'FMCG',
            'LT': 'Infrastructure'
        }
        
        total_value = sum(abs(pos.quantity) * pos.current_price for pos in self.portfolio_manager.positions.values())
        
        for symbol, position in self.portfolio_manager.positions.items():
            sector = sector_mapping.get(symbol, 'Other')
            position_value = abs(position.quantity) * position.current_price
            
            if sector not in sector_exposure:
                sector_exposure[sector] = 0
            
            sector_exposure[sector] += (position_value / total_value) * 100 if total_value > 0 else 0
        
        return sector_exposure
    
    def generate_risk_alerts(self) -> List[str]:
        """Generate risk management alerts"""
        alerts = []
        
        # Check portfolio concentration
        sector_exposure = self.calculate_sector_exposure()
        for sector, exposure in sector_exposure.items():
            if exposure > 40:  # More than 40% in one sector
                alerts.append(f"High concentration in {sector} sector: {exposure:.1f}%")
        
        # Check individual position sizes
        portfolio_value = self.portfolio_manager.get_portfolio_summary()['portfolio_value']
        for symbol, position in self.portfolio_manager.positions.items():
            position_value = abs(position.quantity) * position.current_price
            position_percentage = (position_value / portfolio_value) * 100
            
            if position_percentage > 20:
                alerts.append(f"Large position in {symbol}: {position_percentage:.1f}% of portfolio")
        
        # Check unrealized losses
        for symbol, position in self.portfolio_manager.positions.items():
            if position.unrealized_pnl < 0:
                loss_percentage = abs(position.unrealized_pnl) / (abs(position.quantity) * position.entry_price) * 100
                if loss_percentage > 10:
                    alerts.append(f"Large unrealized loss in {symbol}: {loss_percentage:.1f}%")
        
        return alerts
