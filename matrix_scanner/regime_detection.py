"""
Regime Detection Module

Identifies macro regimes (QE/QT, bull/bear) and narrative awareness
Critical for determining which signals to trust
"""

import pandas as pd
import numpy as np
from yf_cache import history_period_cached
from datetime import datetime, timedelta
try:
    from pandas_datareader import data as pdr
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    print("Warning: pandas_datareader not installed. Fed data will be unavailable.")

class RegimeDetector:
    """
    Detects market regimes based on:
    - Fed policy (QE/QT, rate direction)
    - Sector correlations
    - Wyckoff market cycle phase
    - Narrative shifts
    """
    
    def __init__(self):
        self.regime_history = []
    
    def detect(self, data):
        """
        Main regime detection function
        
        Returns:
        {
            'macro': 'QE Bull' | 'QT Bear' | 'Transitional',
            'fed_policy': 'Easing' | 'Tightening' | 'Neutral',
            'fed_funds_rate': float,
            'rate_direction': 'Rising' | 'Falling' | 'Flat',
            'wyckoff_phase': 'Accumulation' | 'Markup' | 'Distribution' | 'Markdown',
            'sector_correlation': 'Low' | 'High',
            'narrative': str,
            'internals_color': 'Green' | 'Pink' | 'Red',
            'regime_quality': 0-10
        }
        """
        
        result = {
            'macro': self._detect_macro_regime(),
            'fed_policy': self._detect_fed_policy(),
            'fed_funds_rate': self._get_current_fed_rate(),
            'rate_direction': self._get_rate_direction(),
            'wyckoff_phase': self._detect_wyckoff_phase(data),
            'sector_correlation': self._detect_sector_correlation(),
            'narrative': self._assess_narrative(),
            'internals_color': self._assess_internals_color(data),
            'regime_quality': 0
        }
        
        # Calculate overall regime quality (0-10)
        result['regime_quality'] = self._calculate_regime_quality(result)
        
        return result
    
    def _detect_macro_regime(self):
        """
        Detect macro regime (QE/QT, bull/bear)

        Checks:
        - Fed balance sheet size (QE = expanding, QT = contracting)
        - SPX price trend vs 200MA
        - Rate environment
        """

        if not FRED_AVAILABLE:
            return "Unknown"

        try:
            # Fetch Fed balance sheet data (WALCL = All Federal Reserve Banks - Total Assets)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            fed_balance_sheet = pdr.DataReader('WALCL', 'fred', start=start_date, end=end_date)

            if len(fed_balance_sheet) < 90:
                return "Unknown"

            # Check if balance sheet is expanding or contracting
            current_bs = fed_balance_sheet.iloc[-1].values[0]
            three_months_ago_bs = fed_balance_sheet.iloc[-90].values[0] if len(fed_balance_sheet) >= 90 else fed_balance_sheet.iloc[0].values[0]

            bs_change = current_bs - three_months_ago_bs
            bs_direction = "Expanding (QE)" if bs_change > 0 else "Contracting (QT)"

            # Check SPX trend (bull/bear)
            spx = history_period_cached('^GSPC', '1y')
            spx_sma200 = spx['Close'].rolling(200).mean()
            current_spx = spx['Close'].iloc[-1]
            current_sma200 = spx_sma200.iloc[-1]

            market_trend = "Bull" if current_spx > current_sma200 else "Bear"

            # Combine to determine regime
            if bs_change > 0 and market_trend == "Bull":
                regime = "QE Bull"
            elif bs_change > 0 and market_trend == "Bear":
                regime = "QE Bear (Transitional)"
            elif bs_change < 0 and market_trend == "Bull":
                regime = "QT Bull (Fragile)"
            elif bs_change < 0 and market_trend == "Bear":
                regime = "QT Bear"
            else:
                regime = "Transitional"

            return regime

        except Exception as e:
            print(f"Error detecting macro regime: {e}")
            return "Unknown"
    
    def _detect_fed_policy(self):
        """
        Determine Fed policy stance
        
        Check:
        - Recent FOMC statements
        - Rate change trajectory
        - Balance sheet operations
        """
        
        rate_direction = self._get_rate_direction()
        
        if rate_direction == 'Rising':
            return 'Tightening'
        elif rate_direction == 'Falling':
            return 'Easing'
        else:
            return 'Neutral'
    
    def _get_current_fed_rate(self):
        """
        Get current Federal Funds Rate from FRED
        """

        if not FRED_AVAILABLE:
            return None

        try:
            # Fetch Fed Funds Rate (DFF) from FRED
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days

            fed_rate = pdr.DataReader('DFF', 'fred', start=start_date, end=end_date)

            if len(fed_rate) > 0:
                return round(fed_rate.iloc[-1].values[0], 2)
            else:
                return None

        except Exception as e:
            print(f"Error fetching Fed Funds Rate: {e}")
            return None

    def _get_rate_direction(self):
        """
        Determine if rates are rising, falling, or flat

        Compare current rate to 3-month and 6-month ago
        """

        if not FRED_AVAILABLE:
            return "Unknown"

        try:
            # Fetch 6 months of Fed Funds Rate history
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)

            fed_rate = pdr.DataReader('DFF', 'fred', start=start_date, end=end_date)

            if len(fed_rate) < 60:  # Need at least ~2 months of data
                return "Unknown"

            current_rate = fed_rate.iloc[-1].values[0]
            three_months_ago = fed_rate.iloc[-63].values[0] if len(fed_rate) >= 63 else fed_rate.iloc[0].values[0]

            # Calculate change
            rate_change = current_rate - three_months_ago

            # Determine direction (threshold: 0.25% = significant)
            if rate_change > 0.25:
                return "Rising"
            elif rate_change < -0.25:
                return "Falling"
            else:
                return "Flat"

        except Exception as e:
            print(f"Error determining rate direction: {e}")
            return "Unknown"
    
    def _detect_wyckoff_phase(self, data):
        """
        Identify Wyckoff market cycle phase
        
        Phases:
        1. Accumulation - Smart money buying quietly (range-bound, low volume)
        2. Markup - Uptrend (higher highs, higher lows, increasing volume)
        3. Distribution - Smart money selling to retail (range-bound at top, high volume)
        4. Markdown - Downtrend (lower highs, lower lows)
        
        Use price action, volume, and volatility to detect
        """
        
        if len(data) < 100:
            return "Insufficient Data"
        
        # Calculate key metrics
        close = data['Close']
        volume = data['Volume']
        
        # Recent price trend
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        current_price = float(close.iloc[-1])
        current_sma50 = float(sma_50.iloc[-1])
        current_sma200 = float(sma_200.iloc[-1])

        # Volume trend
        avg_volume = float(volume.rolling(50).mean().iloc[-1])
        recent_volume = float(volume.iloc[-20:].mean())
        
        # Simplified phase detection
        if current_price > current_sma50 > current_sma200:
            if recent_volume > avg_volume * 1.2:
                return "Distribution"  # High volume at top
            else:
                return "Markup"  # Uptrend
        elif current_price < current_sma50 < current_sma200:
            return "Markdown"  # Downtrend
        else:
            if recent_volume < avg_volume * 0.8:
                return "Accumulation"  # Low volume consolidation
            else:
                return "Transitional"
        
        # TODO: Enhance with:
        # - Spring/upthrust detection
        # - Trading range analysis
        # - Volume climax identification
        # - SCIN (Supply Coming In) signals
    
    def _detect_sector_correlation(self):
        """
        Detect sector correlation levels
        
        High correlation (2022 bear) = everything moves together (bad for stock pickers)
        Low correlation (healthy bull) = sectors diverge (good for active management)
        
        TODO: Calculate correlation matrix of sector ETFs
        """
        
        # TODO: Fetch sector ETF data (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC)
        # Calculate rolling correlation
        # Return 'Low', 'Medium', or 'High'
        
        return "Unknown"
    
    def _assess_narrative(self):
        """
        Assess prevailing market narrative
        
        This is qualitative and requires:
        - News sentiment analysis
        - Recent FOMC statements
        - Major economic events
        
        Examples:
        - "Inflation fears + rate hikes"
        - "Soft landing narrative"
        - "AI boom"
        - "Banking crisis"
        """
        
        # TODO: Implement narrative detection
        # Could use web scraping of financial news headlines
        # Or sentiment analysis of FOMC minutes
        
        return "Current narrative unknown - implement news analysis"
    
    def _assess_internals_color(self, data):
        """
        Assess market internals "color language"
        
        From the document:
        - Green = healthy internals, breadth strong
        - Pink = deteriorating (like 2022 "pink lily pads" - dying bull)
        - Red = bearish internals
        
        Regime-dependent:
        - Bull regime: green = good, pink = warning
        - Bear regime: any green shoots may be traps
        """
        
        # TODO: Implement by checking:
        # - Breadth thrust success/failure
        # - A/D line divergence
        # - New highs vs new lows
        # - Sector rotation patterns
        
        return "Unknown"
    
    def _calculate_regime_quality(self, regime_data):
        """
        Calculate overall regime quality score (0-10)
        
        Higher quality = more reliable signals
        Lower quality = need extra confirmation
        
        Factors:
        - Fed policy clear direction (not transitional)
        - Wyckoff phase identified
        - Narrative aligns with price action
        - Sector correlation appropriate for phase
        """
        
        score = 5  # Start neutral
        
        # Clear Fed direction
        if regime_data['fed_policy'] in ['Easing', 'Tightening']:
            score += 1
        
        # Identified Wyckoff phase
        if regime_data['wyckoff_phase'] not in ['Insufficient Data', 'Transitional']:
            score += 1
        
        # Known sector correlation
        if regime_data['sector_correlation'] != 'Unknown':
            score += 1
        
        # Internals color identified
        if regime_data['internals_color'] != 'Unknown':
            score += 1
        
        # TODO: Add more quality factors
        
        return min(10, max(0, score))
    
    def check_regime_for_signal(self, signal_type, regime_data):
        """
        Check if a signal is valid in current regime
        
        Examples from document:
        - Zweig Breadth Thrust fails in rising rate environments
        - Bullish stats from 2012-2022 don't work in 1965-1975 stagflation parallels
        - Mean reversion works differently in QE vs QT
        
        Args:
            signal_type: 'zweig_thrust', 'breadth_reversal', etc.
            regime_data: Current regime data dict
        
        Returns:
            bool: True if signal is valid in this regime
        """
        
        # Zweig Thrust validity
        if signal_type == 'zweig_thrust':
            # Fails when Fed is tightening
            if regime_data['rate_direction'] == 'Rising':
                return False
            return True
        
        # Add more signal-regime checks here
        
        return True  # Default to valid
    
    def get_historical_regime_parallel(self):
        """
        Find historical period with similar regime characteristics
        
        Example from document:
        - 2022 conditions similar to 1965-1975 stagflation
        - Use for backtesting filters
        
        Returns period ranges to backtest against
        """
        
        # TODO: Implement regime similarity matching
        # Compare current:
        # - Inflation levels
        # - Rate environment
        # - Market structure (correlation, breadth)
        # - Economic growth
        
        # Against historical periods
        
        return None
