#!/usr/bin/env python3
"""
📈 UNIFIED TRADING MANAGER
Comprehensive trading execution and portfolio management system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import asyncio
import json
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from unified_config import config
from unified_database import db, UnifiedDatabaseManager, PositionRecord, OrderRecord, TradeRecord
from unified_live_data import live_data_manager, LiveQuote
from unified_ai_signals import ai_signal_generator, AISignal

# Setup logging
logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class PositionType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class Order:
    """Trading order"""
    symbol: str
    order_type: OrderType
    side: str  # BUY/SELL
    quantity: int
    order_id: Optional[str] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    timestamp: datetime = None
    filled_timestamp: Optional[datetime] = None
    commission: float = 0.0
    notes: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if not self.order_id:
            self.order_id = str(uuid.uuid4())[:8]

@dataclass
class Position:
    """Trading position"""
    symbol: str
    position_type: PositionType
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    entry_time: datetime = None
    last_update: datetime = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    def __post_init__(self):
        if self.entry_time is None:
            self.entry_time = datetime.now()
        if self.last_update is None:
            self.last_update = datetime.now()

@dataclass
class Trade:
    """Completed trade"""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    commission: float
    entry_time: datetime
    exit_time: datetime
    duration: timedelta
    strategy: str = "AI_SIGNAL"
    notes: str = ""
    
    def __post_init__(self):
        if not self.trade_id:
            self.trade_id = str(uuid.uuid4())[:8]

class RiskManager:
    """Risk management system"""
    
    def __init__(self, max_position_size: float = 0.20, max_portfolio_risk: float = 0.02):
        self.max_position_size = max_position_size  # 20% of portfolio per position
        self.max_portfolio_risk = max_portfolio_risk  # 2% portfolio risk
        self.daily_loss_limit = 0.03  # 3% daily loss limit
        self.max_positions = 10  # Maximum concurrent positions
        
    def calculate_position_size(self, portfolio_value: float, entry_price: float,
                               stop_loss: float, signal_confidence: float) -> int:
        """Calculate optimal position size based on risk management"""
        try:
            # Base position size (% of portfolio)
            base_risk = min(self.max_position_size, signal_confidence / 100 * 0.08)
            
            # Risk per share
            risk_per_share = abs(entry_price - stop_loss) if stop_loss else entry_price * 0.02
            
            # Portfolio risk amount
            risk_amount = portfolio_value * base_risk * self.max_portfolio_risk
            
            # Calculate quantity
            quantity = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
            
            # Ensure minimum viable quantity
            min_quantity = max(1, int(1000 / entry_price))  # At least ₹1000 position
            quantity = max(quantity, min_quantity)
            
            # Ensure maximum position size
            max_quantity = int(portfolio_value * self.max_position_size / entry_price)
            quantity = min(quantity, max_quantity)
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 1
    
    def validate_order(self, order: Order, portfolio_value: float, 
                      current_positions: List[Position]) -> Tuple[bool, str]:
        """Validate order against risk management rules"""
        try:
            # Check portfolio concentration
            if len(current_positions) >= self.max_positions:
                return False, f"Maximum positions limit reached ({self.max_positions})"
            
            # Check position size
            position_value = order.quantity * (order.price or 0)
            if position_value > portfolio_value * self.max_position_size:
                return False, f"Position size exceeds limit ({self.max_position_size*100:.1f}%)"
            
            # Check if already have position in same symbol
            existing_position = next((p for p in current_positions if p.symbol == order.symbol), None)
            if existing_position:
                return False, f"Already have position in {order.symbol}"
            
            # Check minimum order value
            if position_value < 1000:  # Minimum ₹1000 order
                return False, "Order value below minimum (₹1000)"
            
            return True, "Order validated"
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return False, f"Validation error: {str(e)}"

class PaperTradingEngine:
    """Paper trading simulation engine"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.portfolio_value = config.INITIAL_CAPITAL
        self.cash_balance = self.portfolio_value
        self.commission_rate = 0.001  # 0.1% commission
        self.slippage = 0.0005  # 0.05% slippage
        
    def calculate_commission(self, value: float) -> float:
        """Calculate commission for trade"""
        return max(10, value * self.commission_rate)  # Minimum ₹10
    
    def apply_slippage(self, price: float, side: str) -> float:
        """Apply slippage to execution price"""
        if side == 'BUY':
            return price * (1 + self.slippage)
        else:
            return price * (1 - self.slippage)
    
    async def execute_order(self, order: Order) -> bool:
        """Execute order in paper trading"""
        try:
            # Get current market price
            quote = await live_data_manager.get_live_quote(order.symbol)
            if not quote:
                order.status = OrderStatus.REJECTED
                order.notes = "No market data available"
                return False
            
            execution_price = None
            
            # Determine execution price based on order type
            if order.order_type == OrderType.MARKET:
                execution_price = self.apply_slippage(quote.price, order.side)
            
            elif order.order_type == OrderType.LIMIT:
                if order.side == 'BUY' and quote.price <= order.price:
                    execution_price = order.price
                elif order.side == 'SELL' and quote.price >= order.price:
                    execution_price = order.price
            
            elif order.order_type == OrderType.STOP_LOSS:
                if order.side == 'BUY' and quote.price >= order.stop_price:
                    execution_price = self.apply_slippage(quote.price, order.side)
                elif order.side == 'SELL' and quote.price <= order.stop_price:
                    execution_price = self.apply_slippage(quote.price, order.side)
            
            # Execute if price conditions met
            if execution_price:
                trade_value = order.quantity * execution_price
                commission = self.calculate_commission(trade_value)
                
                # Check if sufficient cash for buy orders
                if order.side == 'BUY':
                    total_cost = trade_value + commission
                    if total_cost > self.cash_balance:
                        order.status = OrderStatus.REJECTED
                        order.notes = "Insufficient cash balance"
                        return False
                    
                    self.cash_balance -= total_cost
                else:
                    self.cash_balance += trade_value - commission
                
                # Fill order
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.filled_price = execution_price
                order.filled_timestamp = datetime.now()
                order.commission = commission
                
                logger.info(f"Order executed: {order.side} {order.quantity} {order.symbol} "
                           f"@ ₹{execution_price:.2f}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            order.status = OrderStatus.REJECTED
            order.notes = f"Execution error: {str(e)}"
            return False

class UnifiedTradingManager:
    """Comprehensive trading management system"""
    
    def __init__(self, database: UnifiedDatabaseManager = None):
        self.db = database or db
        self.risk_manager = RiskManager()
        self.paper_engine = PaperTradingEngine()
        
        # Trading state
        self.active_orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.win_rate = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        # Load existing data from database
        self._load_portfolio_state()
        
        logger.info("Unified trading manager initialized")
    
    def _load_portfolio_state(self):
        """Load portfolio state from database"""
        try:
            # Load positions
            positions_df = self.db.get_positions()
            for _, row in positions_df.iterrows():
                position = Position(
                    symbol=row['symbol'],
                    position_type=PositionType(row['position_type']),
                    quantity=int(row['quantity']),
                    avg_price=float(row['avg_price']),
                    current_price=float(row['current_price']),
                    unrealized_pnl=float(row['unrealized_pnl']),
                    realized_pnl=float(row.get('realized_pnl', 0)),
                    entry_time=pd.to_datetime(row['entry_time']),
                    last_update=pd.to_datetime(row['last_update'])
                )
                self.positions[row['symbol']] = position
            
            # Load active orders
            orders_df = self.db.get_orders(status='PENDING')
            for _, row in orders_df.iterrows():
                order = Order(
                    order_id=row['order_id'],
                    symbol=row['symbol'],
                    order_type=OrderType(row['order_type']),
                    side=row['side'],
                    quantity=int(row['quantity']),
                    price=float(row['price']) if row['price'] else None,
                    status=OrderStatus(row['status']),
                    timestamp=pd.to_datetime(row['timestamp'])
                )
                self.active_orders[row['order_id']] = order
            
            logger.info(f"Loaded {len(self.positions)} positions and {len(self.active_orders)} active orders")
            
        except Exception as e:
            logger.error(f"Error loading portfolio state: {e}")
    
    async def update_portfolio_value(self):
        """Update current portfolio value and P&L"""
        try:
            total_value = self.paper_engine.cash_balance
            unrealized_pnl = 0.0
            
            for symbol, position in self.positions.items():
                # Get current quote
                quote = await live_data_manager.get_live_quote(symbol)
                if quote:
                    position.current_price = quote.price
                    position.last_update = datetime.now()
                    
                    # Calculate unrealized P&L
                    if position.position_type == PositionType.LONG:
                        position.unrealized_pnl = (quote.price - position.avg_price) * position.quantity
                    else:
                        position.unrealized_pnl = (position.avg_price - quote.price) * position.quantity
                    
                    unrealized_pnl += position.unrealized_pnl
                    total_value += position.quantity * quote.price
                    
                    # Update position in database
                    position_record = PositionRecord(
                        symbol=position.symbol,
                        position_type=position.position_type.value,
                        quantity=position.quantity,
                        avg_price=position.avg_price,
                        current_price=position.current_price,
                        unrealized_pnl=position.unrealized_pnl,
                        realized_pnl=position.realized_pnl,
                        entry_time=position.entry_time,
                        last_update=position.last_update
                    )
                    self.db.update_position(position_record)
            
            self.paper_engine.portfolio_value = total_value
            self.total_pnl = total_value - config.INITIAL_CAPITAL
            
            logger.debug(f"Portfolio value: ₹{total_value:,.2f}, P&L: ₹{self.total_pnl:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
    
    async def place_order(self, symbol: str, side: str, quantity: int,
                         order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None,
                         stop_price: Optional[float] = None) -> Optional[Order]:
        """Place a trading order"""
        try:
            # For market orders, get current market price
            if order_type == OrderType.MARKET and price is None:
                quote = await live_data_manager.get_live_quote(symbol)
                if quote:
                    price = quote.price
                else:
                    logger.warning(f"No market price available for {symbol}")
                    return None
            
            # Create order
            order = Order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )
            
            # Validate order
            valid, message = self.risk_manager.validate_order(
                order, self.paper_engine.portfolio_value, list(self.positions.values())
            )
            
            if not valid:
                if "minimum" in message:
                    order_value = order.quantity * (order.price or 0)
                    logger.info(f"Order validation failed: {message} (Order value attempted: ₹{order_value:.2f})")
                else:
                    logger.warning(f"Order validation failed: {message}")
                return None
            
            # Add to active orders
            self.active_orders[order.order_id] = order
            
            # Store in database
            order_record = OrderRecord(
                order_id=order.order_id,
                symbol=order.symbol,
                order_type=order.order_type.value,
                side=order.side,
                quantity=order.quantity,
                price=order.price,
                stop_price=order.stop_price,
                status=order.status.value,
                timestamp=order.timestamp
            )
            self.db.store_order(order_record)
            
            # Try to execute immediately if market order
            if order_type == OrderType.MARKET:
                await self._process_order(order)
            
            logger.info(f"Order placed: {side} {quantity} {symbol} @ ₹{price:.2f} ({order_type.value})")
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def _process_order(self, order: Order):
        """Process and execute order"""
        try:
            executed = await self.paper_engine.execute_order(order)
            
            if executed:
                # Update order in database
                order_record = OrderRecord(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    order_type=order.order_type.value,
                    side=order.side,
                    quantity=order.quantity,
                    price=order.price,
                    filled_quantity=order.filled_quantity,
                    filled_price=order.filled_price,
                    status=order.status.value,
                    commission=order.commission,
                    timestamp=order.timestamp,
                    filled_timestamp=order.filled_timestamp
                )
                self.db.update_order(order_record)
                
                # Handle position updates
                await self._update_position_from_order(order)
                
                # Remove from active orders
                if order.order_id in self.active_orders:
                    del self.active_orders[order.order_id]
            
        except Exception as e:
            logger.error(f"Error processing order: {e}")
    
    async def _update_position_from_order(self, order: Order):
        """Update position based on executed order"""
        try:
            symbol = order.symbol
            
            if symbol in self.positions:
                position = self.positions[symbol]
                
                if order.side == 'BUY':
                    # Add to long position or reduce short position
                    if position.position_type == PositionType.LONG:
                        # Increase long position
                        total_cost = (position.quantity * position.avg_price) + \
                                   (order.filled_quantity * order.filled_price)
                        total_quantity = position.quantity + order.filled_quantity
                        position.avg_price = total_cost / total_quantity
                        position.quantity = total_quantity
                    else:
                        # Reduce short position or close and reverse
                        if order.filled_quantity >= position.quantity:
                            # Close short and potentially open long
                            remaining_qty = order.filled_quantity - position.quantity
                            
                            # Record the closed trade
                            await self._record_trade(position, order.filled_price)
                            
                            if remaining_qty > 0:
                                # Open new long position
                                position.position_type = PositionType.LONG
                                position.quantity = remaining_qty
                                position.avg_price = order.filled_price
                            else:
                                # Position closed
                                del self.positions[symbol]
                                return
                        else:
                            # Partially reduce short position
                            position.quantity -= order.filled_quantity
                
                else:  # SELL
                    # Reduce long position or add to short position
                    if position.position_type == PositionType.LONG:
                        if order.filled_quantity >= position.quantity:
                            # Close long and potentially open short
                            remaining_qty = order.filled_quantity - position.quantity
                            
                            # Record the closed trade
                            await self._record_trade(position, order.filled_price)
                            
                            if remaining_qty > 0:
                                # Open new short position
                                position.position_type = PositionType.SHORT
                                position.quantity = remaining_qty
                                position.avg_price = order.filled_price
                            else:
                                # Position closed
                                del self.positions[symbol]
                                return
                        else:
                            # Partially reduce long position
                            position.quantity -= order.filled_quantity
                    else:
                        # Increase short position
                        total_cost = (position.quantity * position.avg_price) + \
                                   (order.filled_quantity * order.filled_price)
                        total_quantity = position.quantity + order.filled_quantity
                        position.avg_price = total_cost / total_quantity
                        position.quantity = total_quantity
            
            else:
                # Create new position
                position_type = PositionType.LONG if order.side == 'BUY' else PositionType.SHORT
                position = Position(
                    symbol=symbol,
                    position_type=position_type,
                    quantity=order.filled_quantity,
                    avg_price=order.filled_price,
                    current_price=order.filled_price,
                    unrealized_pnl=0.0
                )
                self.positions[symbol] = position
            
            # Store/update position in database
            position_record = PositionRecord(
                symbol=position.symbol,
                position_type=position.position_type.value,
                quantity=position.quantity,
                avg_price=position.avg_price,
                current_price=position.current_price,
                unrealized_pnl=position.unrealized_pnl,
                realized_pnl=position.realized_pnl,
                entry_time=position.entry_time,
                last_update=position.last_update
            )
            self.db.store_position(position_record)
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    async def _record_trade(self, position: Position, exit_price: float):
        """Record completed trade"""
        try:
            if position.position_type == PositionType.LONG:
                pnl = (exit_price - position.avg_price) * position.quantity
            else:
                pnl = (position.avg_price - exit_price) * position.quantity
            
            trade = Trade(
                symbol=position.symbol,
                side=position.position_type.value,
                entry_price=position.avg_price,
                exit_price=exit_price,
                quantity=position.quantity,
                pnl=pnl,
                commission=0.0,  # Commission handled in orders
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                duration=datetime.now() - position.entry_time
            )
            
            self.trades.append(trade)
            
            # Update statistics
            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
            self.win_rate = self.winning_trades / self.total_trades
            
            # Store in database
            trade_record = TradeRecord(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                side=trade.side,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                quantity=trade.quantity,
                pnl=trade.pnl,
                commission=trade.commission,
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                strategy=trade.strategy
            )
            self.db.store_trade(trade_record)
            
            logger.info(f"Trade completed: {trade.symbol} P&L: ₹{pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    async def process_ai_signal(self, signal: AISignal) -> bool:
        """Process AI signal and place appropriate orders"""
        try:
            if signal.signal_type == 'HOLD' or signal.confidence < config.MIN_SIGNAL_CONFIDENCE:
                logger.debug(f"Ignoring signal for {signal.symbol}: {signal.signal_type} "
                           f"with {signal.confidence:.1f}% confidence")
                return False
            
            # Check if we already have a position in this symbol
            if signal.symbol in self.positions:
                logger.debug(f"Already have position in {signal.symbol}, skipping signal")
                return False
            
            # Get current quote
            quote = await live_data_manager.get_live_quote(signal.symbol)
            if not quote:
                logger.warning(f"No quote available for {signal.symbol}")
                return False
            
            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                self.paper_engine.portfolio_value,
                quote.price,
                signal.stop_loss,
                signal.confidence
            )
            
            if quantity <= 0:
                logger.warning(f"Invalid position size for {signal.symbol}")
                return False
            
            # Place order
            side = 'BUY' if signal.signal_type == 'BUY' else 'SELL'
            order = await self.place_order(
                symbol=signal.symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.MARKET
            )
            
            if order:
                logger.info(f"Placed order based on AI signal: {side} {quantity} {signal.symbol}")
                
                # Place stop loss order if provided
                if signal.stop_loss and order.status == OrderStatus.FILLED:
                    stop_side = 'SELL' if side == 'BUY' else 'BUY'
                    await self.place_order(
                        symbol=signal.symbol,
                        side=stop_side,
                        quantity=quantity,
                        order_type=OrderType.STOP_LOSS,
                        stop_price=signal.stop_loss
                    )
                    logger.info(f"Placed stop loss order at ₹{signal.stop_loss:.2f}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing AI signal: {e}")
            return False
    
    async def monitor_positions(self):
        """Monitor positions for stop losses and take profits"""
        try:
            for symbol, position in list(self.positions.items()):
                quote = await live_data_manager.get_live_quote(symbol)
                if not quote:
                    continue
                
                # Check stop loss
                if position.stop_loss:
                    should_close = False
                    if position.position_type == PositionType.LONG and quote.price <= position.stop_loss:
                        should_close = True
                    elif position.position_type == PositionType.SHORT and quote.price >= position.stop_loss:
                        should_close = True
                    
                    if should_close:
                        side = 'SELL' if position.position_type == PositionType.LONG else 'BUY'
                        await self.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=position.quantity,
                            order_type=OrderType.MARKET
                        )
                        logger.info(f"Stop loss triggered for {symbol} at ₹{quote.price:.2f}")
                
                # Check take profit
                if position.take_profit:
                    should_close = False
                    if position.position_type == PositionType.LONG and quote.price >= position.take_profit:
                        should_close = True
                    elif position.position_type == PositionType.SHORT and quote.price <= position.take_profit:
                        should_close = True
                    
                    if should_close:
                        side = 'SELL' if position.position_type == PositionType.LONG else 'BUY'
                        await self.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=position.quantity,
                            order_type=OrderType.MARKET
                        )
                        logger.info(f"Take profit triggered for {symbol} at ₹{quote.price:.2f}")
                        
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    async def process_pending_orders(self):
        """Process pending limit and stop orders"""
        try:
            for order_id, order in list(self.active_orders.items()):
                if order.status == OrderStatus.PENDING:
                    await self._process_order(order)
                    
        except Exception as e:
            logger.error(f"Error processing pending orders: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        total_positions_value = sum(
            pos.quantity * pos.current_price for pos in self.positions.values()
        )
        
        # Convert positions to serializable format
        positions_list = []
        for pos in self.positions.values():
            positions_list.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_price': pos.avg_price,
                'current_price': pos.current_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'realized_pnl': pos.realized_pnl,
                'position_type': pos.position_type.value if hasattr(pos.position_type, 'value') else str(pos.position_type),
                'entry_time': pos.entry_time.isoformat() if hasattr(pos.entry_time, 'isoformat') else str(pos.entry_time),
                'last_update': pos.last_update.isoformat() if hasattr(pos.last_update, 'isoformat') else str(pos.last_update)
            })
        
        # Convert orders to serializable format
        orders_list = []
        for order in self.active_orders.values():
            orders_list.append({
                'order_id': order.order_id,
                'symbol': order.symbol,
                'order_type': order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type),
                'side': order.side,
                'quantity': order.quantity,
                'price': order.price,
                'status': order.status.value if hasattr(order.status, 'value') else str(order.status),
                'timestamp': order.timestamp.isoformat() if hasattr(order.timestamp, 'isoformat') else str(order.timestamp)
            })
        
        return {
            'portfolio_value': self.paper_engine.portfolio_value,
            'cash_balance': self.paper_engine.cash_balance,
            'positions_value': total_positions_value,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'total_positions': len(self.positions),
            'active_orders': len(self.active_orders),
            'total_trades': self.total_trades,
            'win_rate': self.win_rate * 100 if self.win_rate else 0,
            'positions': positions_list,
            'active_orders': orders_list
        }

# Create global trading manager instance
trading_manager = UnifiedTradingManager()

if __name__ == "__main__":
    print("📈 UNIFIED TRADING MANAGER")
    print("=" * 50)
    
    async def test_trading_manager():
        print("Testing trading manager...")
        
        # Update portfolio value
        await trading_manager.update_portfolio_value()
        
        # Get portfolio summary
        summary = trading_manager.get_portfolio_summary()
        print(f"✅ Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
        print(f"   Cash Balance: ₹{summary['cash_balance']:,.2f}")
        print(f"   Total P&L: ₹{summary['total_pnl']:,.2f}")
        print(f"   Positions: {summary['total_positions']}")
        print(f"   Active Orders: {summary['active_orders']}")
        
        # Test order placement
        print("\nTesting order placement...")
        order = await trading_manager.place_order(
            symbol='RELIANCE',
            side='BUY',
            quantity=10,
            order_type=OrderType.MARKET
        )
        
        if order:
            print(f"✅ Order placed: {order.order_id}")
            print(f"   Status: {order.status.value}")
            if order.status == OrderStatus.FILLED:
                print(f"   Filled at: ₹{order.filled_price:.2f}")
        
        # Test AI signal processing
        print("\nTesting AI signal processing...")
        signals = await ai_signal_generator.generate_signals_for_watchlist()
        
        buy_signals = [s for s in signals if s.signal_type == 'BUY' and s.confidence > 60]
        
        if buy_signals:
            signal = buy_signals[0]
            processed = await trading_manager.process_ai_signal(signal)
            print(f"✅ Processed AI signal for {signal.symbol}: {processed}")
        
        # Final portfolio summary
        summary = trading_manager.get_portfolio_summary()
        print(f"\nFinal Portfolio Summary:")
        print(f"   Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
        print(f"   Total Positions: {summary['total_positions']}")
        print(f"   Total Trades: {summary['total_trades']}")
    
    # Run test
    asyncio.run(test_trading_manager())
    print("✅ Trading manager ready!")
    print("=" * 50)
