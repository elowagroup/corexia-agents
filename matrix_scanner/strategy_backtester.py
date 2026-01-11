"""
Strategy Backtester

Tests how different strategies have performed historically on this specific ticker
Critical for weighting strategies by what actually works for each stock
"""

import pandas as pd
import numpy as np
from ma_system import MovingAverageSystem
from technical_analysis import TechnicalAnalyzer
from numerology import SequenceMap

class StrategyBacktester:
    """
    Backtests multiple strategies on historical data
    
    Strategies:
    - 10/50/200 MA System
    - 2B Pattern
    - Sequence Level Trades
    - Market Memory Zone Trades
    
    Returns win rate, avg return, best timeframe for each
    """
    
    def __init__(self):
        self.strategies = {
            '10_50_200': self._backtest_ma_system,
            '2b_pattern': self._backtest_2b,
            'sequence_trades': self._backtest_sequence,
            'memory_zones': self._backtest_memory_zones
        }
    
    def run_all_strategies(self, ticker, data):
        """
        Run all strategy backtests
        
        Returns:
        {
            'strategy_name': {
                'win_rate': float (0-100),
                'avg_return': float (% per trade),
                'total_trades': int,
                'best_timeframe': str,
                'regime_stats': dict
            }
        }
        """
        
        results = {}
        
        for strategy_name, backtest_func in self.strategies.items():
            try:
                results[strategy_name] = backtest_func(data)
            except Exception as e:
                results[strategy_name] = {
                    'win_rate': 0,
                    'avg_return': 0,
                    'total_trades': 0,
                    'best_timeframe': 'N/A',
                    'error': str(e)
                }
        
        return results
    
    def _backtest_ma_system(self, data):
        """
        Backtest the 10/50/200 MA crossover system
        
        Simulates actual trades following the rules
        """
        
        if len(data) < 200:
            return {
                'win_rate': 0,
                'avg_return': 0,
                'total_trades': 0,
                'best_timeframe': 'Insufficient data'
            }
        
        ma_system = MovingAverageSystem()
        
        # Add MAs to data
        data_with_mas = ma_system._calculate_mas(data)
        
        trades = []
        in_position = False
        entry_price = 0
        entry_type = None
        
        for i in range(1, len(data_with_mas)):
            current = data_with_mas.iloc[i]
            previous = data_with_mas.iloc[i-1]
            
            # Skip if not enough data
            if pd.isna(current['SMA200']):
                continue
            
            regime = ma_system._detect_regime(current)
            signal = ma_system._detect_signal(current, previous, regime)
            
            # Entry logic
            if not in_position:
                if signal == 'Long' and ma_system._check_entry_valid(current, signal, regime):
                    in_position = True
                    entry_price = current['Close']
                    entry_type = 'Long'
                
                elif signal == 'Short' and ma_system._check_entry_valid(current, signal, regime):
                    in_position = True
                    entry_price = current['Close']
                    entry_type = 'Short'
            
            # Exit logic
            else:
                exit_triggered = False
                exit_price = current['Close']
                
                if entry_type == 'Long':
                    if signal == 'Exit Long' or current['SMA10'] < current['SMA50']:
                        exit_triggered = True
                
                elif entry_type == 'Short':
                    if signal == 'Exit Short' or current['SMA10'] > current['SMA50']:
                        exit_triggered = True
                
                if exit_triggered:
                    # Calculate return
                    if entry_type == 'Long':
                        return_pct = ((exit_price - entry_price) / entry_price) * 100
                    else:
                        return_pct = ((entry_price - exit_price) / entry_price) * 100
                    
                    trades.append({
                        'entry': entry_price,
                        'exit': exit_price,
                        'type': entry_type,
                        'return': return_pct,
                        'win': return_pct > 0
                    })
                    
                    in_position = False
        
        # Calculate statistics
        if len(trades) == 0:
            return {
                'win_rate': 0,
                'avg_return': 0,
                'total_trades': 0,
                'best_timeframe': 'No trades executed'
            }
        
        wins = sum(1 for t in trades if t['win'])
        win_rate = (wins / len(trades)) * 100
        avg_return = np.mean([t['return'] for t in trades])
        
        return {
            'win_rate': round(win_rate, 1),
            'avg_return': round(avg_return, 2),
            'total_trades': len(trades),
            'best_timeframe': 'Daily',  # Default for now
            'trades': trades[-10:]  # Last 10 trades for reference
        }
    
    def _backtest_2b(self, data):
        """
        Backtest 2B pattern trades
        
        Enter when 2B detected, exit on opposite 2B or after N bars
        """
        
        if len(data) < 50:
            return {
                'win_rate': 0,
                'avg_return': 0,
                'total_trades': 0,
                'best_timeframe': 'Insufficient data'
            }
        
        technical = TechnicalAnalyzer()
        
        trades = []
        
        # Scan through data looking for 2B patterns
        for i in range(20, len(data) - 5):
            # Get window of data
            window = data.iloc[i-20:i+1]
            
            # Check for 2B
            is_2b = technical._detect_2b(window)
            
            if is_2b:
                entry_price = data.iloc[i]['Close']
                
                # Hold for 5 bars or until opposite signal
                exit_idx = min(i + 5, len(data) - 1)
                exit_price = data.iloc[exit_idx]['Close']
                
                # Assume bullish 2B if current close > entry
                # TODO: Improve direction detection
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'return': return_pct,
                    'win': return_pct > 0
                })
        
        if len(trades) == 0:
            return {
                'win_rate': 0,
                'avg_return': 0,
                'total_trades': 0,
                'best_timeframe': 'No 2B patterns found'
            }
        
        wins = sum(1 for t in trades if t['win'])
        win_rate = (wins / len(trades)) * 100
        avg_return = np.mean([t['return'] for t in trades])
        
        return {
            'win_rate': round(win_rate, 1),
            'avg_return': round(avg_return, 2),
            'total_trades': len(trades),
            'best_timeframe': 'Daily'
        }
    
    def _backtest_sequence(self, data):
        """
        Backtest trades at Sequence Map levels
        
        Enter when price hits Holy Trinity or palindrome
        Exit after move to next sequence level
        """
        
        if len(data) < 50:
            return {
                'win_rate': 0,
                'avg_return': 0,
                'total_trades': 0,
                'best_timeframe': 'Insufficient data'
            }
        
        sequence = SequenceMap()
        
        trades = []
        
        for i in range(10, len(data) - 3):
            current_price = data.iloc[i]['Close']
            
            # Analyze sequence
            analysis = sequence.analyze(current_price)
            
            # Trade on Holy Trinity or strong palindrome
            if analysis['is_holy_trinity'] or (analysis['is_palindrome'] and analysis['palindrome_power'] >= 2):
                entry_price = current_price
                
                # Exit after 3 bars or at next magnet
                exit_idx = i + 3
                if exit_idx >= len(data):
                    continue
                
                exit_price = data.iloc[exit_idx]['Close']
                
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'return': return_pct,
                    'win': abs(return_pct) > 1  # At least 1% move
                })
        
        if len(trades) == 0:
            return {
                'win_rate': 0,
                'avg_return': 0,
                'total_trades': 0,
                'best_timeframe': 'No sequence levels hit'
            }
        
        wins = sum(1 for t in trades if t['win'])
        win_rate = (wins / len(trades)) * 100
        avg_return = np.mean([t['return'] for t in trades])
        
        return {
            'win_rate': round(win_rate, 1),
            'avg_return': round(avg_return, 2),
            'total_trades': len(trades),
            'best_timeframe': 'Daily'
        }
    
    def _backtest_memory_zones(self, data):
        """
        Backtest trades at Market Memory zones
        
        TODO: Implement once memory zones are defined
        Requires proxy data (breadth, VIX, ratios)
        """
        
        return {
            'win_rate': 0,
            'avg_return': 0,
            'total_trades': 0,
            'best_timeframe': 'Not implemented - requires proxy data'
        }
    
    def compare_regime_performance(self, trades, data):
        """
        Compare strategy performance in different regimes
        
        Bull vs Bear vs QE vs QT
        
        Returns regime-specific statistics
        """
        
        # TODO: Implement regime classification for historical data
        # Then filter trades by regime and calculate separate stats
        
        return {
            'bull_regime': {},
            'bear_regime': {},
            'qe_regime': {},
            'qt_regime': {}
        }
    
    def get_best_timeframe(self, ticker):
        """
        Determine which timeframe works best for this ticker
        
        Test Daily vs Hourly vs 15min
        
        Returns: '1D', '1H', or '15M'
        """
        
        # TODO: Fetch multiple timeframes and compare
        # For now, default to Daily
        
        return '1D'
