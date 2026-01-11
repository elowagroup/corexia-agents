"""
10/50/200 SMA Crossover Trading System

100% mechanical, market-agnostic, timeframe-agnostic trend-following system
From the complete manual in the sacred document

ONLY trades when:
- Bull Regime: close > SMA200 AND SMA50 > SMA200
- Bear Regime: close < SMA200 AND SMA50 < SMA200
"""

import pandas as pd
import numpy as np

class MovingAverageSystem:
    """
    10/50/200 Simple Moving Average crossover system
    
    Pure trend-following with strict regime filters
    Never enters against the 200-period trend
    """
    
    def __init__(self):
        self.ma_periods = {
            'sma10': 10,
            'sma50': 50,
            'sma200': 200
        }
    
    def analyze(self, data):
        """
        Main analysis function
        
        Returns:
        {
            'regime': 'Bull' | 'Bear' | 'Neutral',
            'sma10': float,
            'sma50': float,
            'sma200': float,
            'signal': 'Long' | 'Short' | 'Exit Long' | 'Exit Short' | 'None',
            'entry_valid': bool,
            'exit_triggered': bool,
            'stop_level': float,
            'position_size_factor': float (adjusted for volatility)
        }
        """
        
        # Calculate moving averages
        data = self._calculate_mas(data)
        
        # Get current values
        current = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else current
        
        # Detect regime
        regime = self._detect_regime(current)
        
        # Detect crossovers
        signal = self._detect_signal(current, previous, regime)
        
        # Check entry validity
        entry_valid = self._check_entry_valid(current, signal, regime)
        
        # Check exit conditions
        exit_triggered = self._check_exit_conditions(data, regime)
        
        # Calculate stop level
        stop_level = self._calculate_stop(data, signal)
        
        # Volatility adjustment
        position_size_factor = self._calculate_position_size_factor(data)
        
        return {
            'regime': regime,
            'sma10': current['SMA10'],
            'sma50': current['SMA50'],
            'sma200': current['SMA200'],
            'signal': signal,
            'entry_valid': entry_valid,
            'exit_triggered': exit_triggered,
            'stop_level': stop_level,
            'position_size_factor': position_size_factor,
            'current_close': current['Close']
        }
    
    def _calculate_mas(self, data):
        """Calculate Simple Moving Averages"""
        
        df = data.copy()
        
        df['SMA10'] = df['Close'].rolling(window=10).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        return df
    
    def _detect_regime(self, current):
        """
        Classify current regime
        
        Bull Regime: close > SMA200 AND SMA50 > SMA200
        Bear Regime: close < SMA200 AND SMA50 < SMA200
        Neutral Regime: anything else (no trades)
        """
        
        close = current['Close']
        sma50 = current['SMA50']
        sma200 = current['SMA200']
        
        # Check for NaN (not enough data)
        if pd.isna(sma200):
            return 'Neutral'
        
        # Bull regime
        if close > sma200 and sma50 > sma200:
            return 'Bull'
        
        # Bear regime
        elif close < sma200 and sma50 < sma200:
            return 'Bear'
        
        # Neutral (choppy, no clear trend)
        else:
            return 'Neutral'
    
    def _detect_signal(self, current, previous, regime):
        """
        Detect crossover signals
        
        Long: SMA10 crosses above SMA50 (in Bull regime)
        Short: SMA10 crosses below SMA50 (in Bear regime)
        """
        
        # Check for crossovers
        sma10_curr = current['SMA10']
        sma50_curr = current['SMA50']
        sma10_prev = previous['SMA10']
        sma50_prev = previous['SMA50']
        
        # Check for NaN
        if any(pd.isna(x) for x in [sma10_curr, sma50_curr, sma10_prev, sma50_prev]):
            return 'None'
        
        bull_cross = sma10_prev <= sma50_prev and sma10_curr > sma50_curr
        bear_cross = sma10_prev >= sma50_prev and sma10_curr < sma50_curr

        if bull_cross:
            return 'Long' if regime == 'Bull' else 'Exit Short'

        if bear_cross:
            return 'Short' if regime == 'Bear' else 'Exit Long'
        
        return 'None'
    
    def _check_entry_valid(self, current, signal, regime):
        """
        Check if entry is valid according to strict rules
        
        Long entry valid ONLY when:
        - SMA10 crosses above SMA50
        - SMA50 > SMA200
        - Close > SMA200
        
        Short entry valid ONLY when:
        - SMA10 crosses below SMA50
        - SMA50 < SMA200
        - Close < SMA200
        """
        
        close = current['Close']
        sma50 = current['SMA50']
        sma200 = current['SMA200']
        
        if signal == 'Long':
            return close > sma200 and sma50 > sma200
        
        elif signal == 'Short':
            return close < sma200 and sma50 < sma200
        
        return False
    
    def _check_exit_conditions(self, data, regime):
        """
        Check if any exit conditions are triggered
        
        Exit Long when:
        - SMA10 crosses below SMA50, OR
        - SMA50 crosses below SMA200, OR
        - Close below SMA200 for 2 consecutive bars
        
        Exit Short when:
        - SMA10 crosses above SMA50, OR
        - SMA50 crosses above SMA200, OR
        - Close above SMA200 for 2 consecutive bars
        """
        
        if len(data) < 2:
            return False
        
        current = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Long exit conditions
        if regime == 'Bull':
            # 10/50 death cross
            if current['SMA10'] < current['SMA50']:
                return True
            
            # 50/200 death cross
            if current['SMA50'] < current['SMA200']:
                return True
            
            # Two closes below 200
            if current['Close'] < current['SMA200'] and previous['Close'] < previous['SMA200']:
                return True
        
        # Short exit conditions
        elif regime == 'Bear':
            # 10/50 golden cross
            if current['SMA10'] > current['SMA50']:
                return True
            
            # 50/200 golden cross
            if current['SMA50'] > current['SMA200']:
                return True
            
            # Two closes above 200
            if current['Close'] > current['SMA200'] and previous['Close'] > previous['SMA200']:
                return True
        
        return False
    
    def _calculate_stop(self, data, signal):
        """
        Calculate initial protective stop
        
        Longs: lower of (signal bar low OR SMA50 - 1×ATR)
        Shorts: higher of (signal bar high OR SMA50 + 1×ATR)
        """
        
        if len(data) < 14:
            return None
        
        current = data.iloc[-1]
        
        # Calculate ATR(14)
        atr = self._calculate_atr(data, period=14)
        
        if signal == 'Long':
            stop_from_low = current['Low']
            stop_from_ma = current['SMA50'] - atr
            return max(stop_from_low, stop_from_ma)
        
        elif signal == 'Short':
            stop_from_high = current['High']
            stop_from_ma = current['SMA50'] + atr
            return min(stop_from_high, stop_from_ma)
        
        return None
    
    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR is SMA of True Range
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def _calculate_position_size_factor(self, data):
        """
        Volatility adjustment for position sizing
        
        If current ATR > 2× average ATR over last 100 periods,
        reduce position size by 50% (return 0.5)
        
        Otherwise return 1.0 (full size)
        """
        
        if len(data) < 100:
            return 1.0
        
        current_atr = self._calculate_atr(data, period=14)
        
        # Calculate ATR for each of last 100 periods
        atr_series = []
        for i in range(100):
            if len(data) - i >= 14:
                historical_data = data.iloc[:-(i+1)] if i > 0 else data
                atr_val = self._calculate_atr(historical_data, period=14)
                atr_series.append(atr_val)
        
        avg_atr = np.mean(atr_series)
        
        # If current volatility is more than 2x average, reduce size
        if current_atr > 2 * avg_atr:
            return 0.5
        
        return 1.0
    
    def get_regime(self, data):
        """Simple function to just get the regime"""
        data = self._calculate_mas(data)
        current = data.iloc[-1]
        return self._detect_regime(current)
    
    def get_signals(self, data):
        """Simple function to get just the signals"""
        analysis = self.analyze(data)
        return {
            'signal': analysis['signal'],
            'entry_valid': analysis['entry_valid']
        }
    
    def generate_trade_plan(self, analysis, risk_percent=1.5):
        """
        Generate complete trade plan with entry, stop, and sizing
        
        Args:
            analysis: Result from analyze()
            risk_percent: Risk per trade (default 1.5%)
        
        Returns:
            Trade plan dict
        """
        
        if not analysis['entry_valid']:
            return {
                'tradeable': False,
                'reason': 'Entry conditions not met'
            }
        
        entry_price = analysis['current_close']
        stop_price = analysis['stop_level']
        
        if stop_price is None:
            return {
                'tradeable': False,
                'reason': 'Cannot calculate stop level'
            }
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_price)
        
        # Position sizing (assumes $100k account, adjust as needed)
        account_size = 100000  # Placeholder
        dollar_risk = account_size * (risk_percent / 100)
        
        shares = int(dollar_risk / risk_per_share)
        
        # Apply volatility adjustment
        shares = int(shares * analysis['position_size_factor'])
        
        # Calculate targets (simple 2R and 3R)
        if analysis['signal'] == 'Long':
            target_1 = entry_price + (2 * risk_per_share)
            target_2 = entry_price + (3 * risk_per_share)
        else:
            target_1 = entry_price - (2 * risk_per_share)
            target_2 = entry_price - (3 * risk_per_share)
        
        return {
            'tradeable': True,
            'signal': analysis['signal'],
            'regime': analysis['regime'],
            'entry': entry_price,
            'stop': stop_price,
            'target_1': target_1,
            'target_2': target_2,
            'shares': shares,
            'dollar_risk': dollar_risk,
            'risk_per_share': risk_per_share,
            'risk_reward_1': 2.0,
            'risk_reward_2': 3.0
        }
