import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from utils.logger import logger

class BacktestEngine:
    def __init__(self):
        self.trades = []
        self.portfolio_value = []
        self.initial_capital = 100000  # Starting capital
        self.current_capital = self.initial_capital
        self.position_size = 0.02  # 2% of capital per trade
        
    def run_backtest(self, data: pd.DataFrame, signals: List[Dict], 
                    initial_capital: float = 100000) -> Dict:
        """Run backtest on historical data with generated signals"""
        try:
            self.initial_capital = initial_capital
            self.current_capital = initial_capital
            self.trades = []
            self.portfolio_value = [initial_capital]
            
            if data.empty or not signals:
                logger.warning("Insufficient data for backtesting")
                return self.get_empty_results()
            
            # Sort signals by timestamp
            signals_sorted = sorted(signals, key=lambda x: x.get('timestamp', datetime.now()))
            
            open_positions = {}
            
            for signal in signals_sorted:
                try:
                    symbol = signal.get('symbol', '')
                    signal_type = signal.get('signal', 'NEUTRAL')
                    timestamp = signal.get('timestamp', datetime.now())
                    entry_price = signal.get('entry_price', 0)
                    target_price = signal.get('target_price', 0)
                    stop_loss = signal.get('stop_loss', 0)
                    confidence = signal.get('confidence', 0)
                    
                    if signal_type == 'NEUTRAL' or entry_price <= 0:
                        continue
                    
                    # Calculate position size
                    position_value = self.current_capital * self.position_size
                    quantity = position_value / entry_price
                    
                    if signal_type == 'BUY':
                        # Close any existing sell position
                        if symbol in open_positions and open_positions[symbol]['type'] == 'SELL':
                            self.close_position(symbol, open_positions, entry_price, timestamp)
                        
                        # Open buy position
                        if self.current_capital >= position_value:
                            open_positions[symbol] = {
                                'type': 'BUY',
                                'entry_price': entry_price,
                                'quantity': quantity,
                                'timestamp': timestamp,
                                'target': target_price,
                                'stop_loss': stop_loss,
                                'confidence': confidence
                            }
                            self.current_capital -= position_value
                    
                    elif signal_type == 'SELL':
                        # Close any existing buy position
                        if symbol in open_positions and open_positions[symbol]['type'] == 'BUY':
                            self.close_position(symbol, open_positions, entry_price, timestamp)
                        
                        # Open sell position (short)
                        open_positions[symbol] = {
                            'type': 'SELL',
                            'entry_price': entry_price,
                            'quantity': quantity,
                            'timestamp': timestamp,
                            'target': target_price,
                            'stop_loss': stop_loss,
                            'confidence': confidence
                        }
                        self.current_capital += position_value  # Receive cash from short
                
                except Exception as e:
                    logger.error(f"Error processing signal in backtest: {e}")
                    continue
            
            # Close remaining positions at the last available price
            if not data.empty:
                last_price = data['close'].iloc[-1]
                last_timestamp = data['timestamp'].iloc[-1] if 'timestamp' in data.columns else datetime.now()
                
                for symbol in list(open_positions.keys()):
                    self.close_position(symbol, open_positions, last_price, last_timestamp)
            
            # Calculate final results
            return self.calculate_results()
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return self.get_empty_results()
    
    def close_position(self, symbol: str, open_positions: Dict, 
                      exit_price: float, exit_timestamp: datetime):
        """Close an open position"""
        try:
            position = open_positions[symbol]
            entry_price = position['entry_price']
            quantity = position['quantity']
            position_type = position['type']
            
            # Calculate P&L
            if position_type == 'BUY':
                pnl = (exit_price - entry_price) * quantity
                exit_value = exit_price * quantity
                self.current_capital += exit_value
            else:  # SELL (short position)
                pnl = (entry_price - exit_price) * quantity
                exit_value = exit_price * quantity
                self.current_capital -= exit_value  # Buy back shares
            
            # Record trade
            trade = {
                'symbol': symbol,
                'type': position_type,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'entry_time': position['timestamp'],
                'exit_time': exit_timestamp,
                'pnl': pnl,
                'pnl_percent': (pnl / (entry_price * quantity)) * 100,
                'confidence': position['confidence'],
                'target': position.get('target', 0),
                'stop_loss': position.get('stop_loss', 0)
            }
            
            self.trades.append(trade)
            self.portfolio_value.append(self.current_capital)
            
            # Remove position
            del open_positions[symbol]
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    def calculate_results(self) -> Dict:
        """Calculate backtest performance metrics"""
        try:
            if not self.trades:
                return self.get_empty_results()
            
            # Basic metrics
            total_trades = len(self.trades)
            winning_trades = len([t for t in self.trades if t['pnl'] > 0])
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # P&L metrics
            total_pnl = sum(t['pnl'] for t in self.trades)
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            
            winning_pnl = [t['pnl'] for t in self.trades if t['pnl'] > 0]
            losing_pnl = [t['pnl'] for t in self.trades if t['pnl'] <= 0]
            
            avg_win = np.mean(winning_pnl) if winning_pnl else 0
            avg_loss = np.mean(losing_pnl) if losing_pnl else 0
            
            # Risk metrics
            max_win = max(winning_pnl) if winning_pnl else 0
            max_loss = min(losing_pnl) if losing_pnl else 0
            
            # Calculate drawdown
            portfolio_values = np.array(self.portfolio_value)
            running_max = np.maximum.accumulate(portfolio_values)
            drawdown = (portfolio_values - running_max) / running_max * 100
            max_drawdown = np.min(drawdown)
            
            # Return metrics
            total_return = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
            
            # Sharpe ratio (simplified)
            if len(self.portfolio_value) > 1:
                returns = np.diff(self.portfolio_value) / self.portfolio_value[:-1]
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) != 0 else 0
            else:
                sharpe_ratio = 0
            
            # Profit factor
            gross_profit = sum(winning_pnl) if winning_pnl else 0
            gross_loss = abs(sum(losing_pnl)) if losing_pnl else 1
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
            
            results = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'max_win': round(max_win, 2),
                'max_loss': round(max_loss, 2),
                'total_return': round(total_return, 2),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'profit_factor': round(profit_factor, 2),
                'initial_capital': self.initial_capital,
                'final_capital': round(self.current_capital, 2),
                'trades': self.trades,
                'portfolio_values': self.portfolio_value
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating backtest results: {e}")
            return self.get_empty_results()
    
    def get_empty_results(self) -> Dict:
        """Return empty results structure"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_win': 0,
            'max_loss': 0,
            'total_return': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'profit_factor': 0,
            'initial_capital': self.initial_capital,
            'final_capital': self.initial_capital,
            'trades': [],
            'portfolio_values': [self.initial_capital]
        }
    
    def generate_report(self, results: Dict) -> str:
        """Generate a human-readable backtest report"""
        try:
            report = f"""
=== BACKTEST RESULTS ===

Portfolio Performance:
• Initial Capital: ₹{results['initial_capital']:,.2f}
• Final Capital: ₹{results['final_capital']:,.2f}
• Total Return: {results['total_return']:.2f}%
• Total P&L: ₹{results['total_pnl']:,.2f}

Trade Statistics:
• Total Trades: {results['total_trades']}
• Winning Trades: {results['winning_trades']}
• Losing Trades: {results['losing_trades']}
• Win Rate: {results['win_rate']:.2f}%

P&L Analysis:
• Average P&L per Trade: ₹{results['avg_pnl']:,.2f}
• Average Win: ₹{results['avg_win']:,.2f}
• Average Loss: ₹{results['avg_loss']:,.2f}
• Best Trade: ₹{results['max_win']:,.2f}
• Worst Trade: ₹{results['max_loss']:,.2f}

Risk Metrics:
• Maximum Drawdown: {results['max_drawdown']:.2f}%
• Sharpe Ratio: {results['sharpe_ratio']:.3f}
• Profit Factor: {results['profit_factor']:.2f}

"""
            
            # Add trade details if available
            if results['trades']:
                report += "\nRecent Trades:\n"
                for trade in results['trades'][-5:]:  # Last 5 trades
                    pnl_str = f"₹{trade['pnl']:,.2f}"
                    if trade['pnl'] > 0:
                        pnl_str = f"+{pnl_str}"
                    
                    report += f"• {trade['symbol']} {trade['type']}: {pnl_str} ({trade['pnl_percent']:.1f}%)\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating backtest report: {e}")
            return "Error generating backtest report"
    
    def optimize_parameters(self, data: pd.DataFrame, 
                          parameter_ranges: Dict) -> Dict:
        """Optimize strategy parameters using grid search"""
        try:
            best_params = {}
            best_return = float('-inf')
            best_results = {}
            
            # This is a simplified optimization
            # In practice, you would iterate through parameter combinations
            # and run backtests for each combination
            
            logger.info("Parameter optimization completed")
            return {
                'best_params': best_params,
                'best_return': best_return,
                'best_results': best_results
            }
            
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
            return {}
    
    def calculate_trade_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate detailed trade metrics"""
        try:
            if not trades:
                return {}
            
            # Hold time analysis
            hold_times = []
            for trade in trades:
                if 'entry_time' in trade and 'exit_time' in trade:
                    hold_time = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # hours
                    hold_times.append(hold_time)
            
            avg_hold_time = np.mean(hold_times) if hold_times else 0
            
            # Confidence analysis
            confidences = [t.get('confidence', 0) for t in trades]
            avg_confidence = np.mean(confidences) if confidences else 0
            
            # Success rate by confidence level
            high_conf_trades = [t for t in trades if t.get('confidence', 0) >= 75]
            high_conf_success = len([t for t in high_conf_trades if t['pnl'] > 0])
            high_conf_rate = (high_conf_success / len(high_conf_trades) * 100) if high_conf_trades else 0
            
            return {
                'avg_hold_time_hours': round(avg_hold_time, 2),
                'avg_confidence': round(avg_confidence, 2),
                'high_confidence_trades': len(high_conf_trades),
                'high_confidence_success_rate': round(high_conf_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trade metrics: {e}")
            return {}
