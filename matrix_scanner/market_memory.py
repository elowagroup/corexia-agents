"""
Market Memory Analyzer - Proxy-based breadth, volatility, and intermarket zones

This module identifies persistent horizontal "memories" in breadth, ratios, internals,
and volatility where the market has reversed or stalled repeatedly.
"""

import pandas as pd
import numpy as np
import yfinance as yf

class MarketMemoryAnalyzer:
    """
    Analyzes market memory zones from proxies (not price directly)
    - Breadth indicators (NYSE % above 50DMA, NYMO, etc.)
    - Intermarket ratios (NDX:SPX, IWC:OEX, etc.)
    - Volatility (VIX, VIX9D, VVIX)
    - DXY and sector correlations
    """
    
    def __init__(self):
        self.breadth_zones = self._initialize_breadth_zones()
        self.ratio_zones = self._initialize_ratio_zones()
        self.volatility_zones = self._initialize_volatility_zones()
    
    def _initialize_breadth_zones(self):
        """Define Market Memory zones for breadth indicators"""
        return {
            'nyse_above_50dma': {
                'red_sell_zone': (75, 80),  # Tops in 2022
                'green_buy_zone': (15, 25),  # Bottoms
                'description': 'Percentage of NYSE stocks above 50DMA'
            },
            'zweig_thrust': {
                'threshold_low': 5,
                'threshold_high': 90,
                'timeframe_days': 15,
                'description': 'Zweig Breadth Thrust signal'
            }
        }
    
    def _initialize_ratio_zones(self):
        """Define Market Memory zones for intermarket ratios"""
        return {
            'ndx_spx': {
                'description': 'NDX:SPX ratio - tech leadership',
                'multi_decade_trendline': None,  # Will be calculated
                'current_value': None
            },
            'iwc_oex': {
                'description': 'IWC:OEX ratio - small cap vs large cap',
                'memory_levels': [],  # Historical support/resistance
                'current_value': None
            }
        }
    
    def _initialize_volatility_zones(self):
        """Define Market Memory zones for volatility"""
        return {
            'vix': {
                'red_overbought': 30,  # Typical extreme high
                'green_oversold': 12,   # Typical extreme low
                'description': 'VIX Market Memory zones'
            },
            'vix9d': {
                'red_zone': (25, 35),
                'green_zone': (10, 15),
                'description': 'VIX9D short-term variant zones'
            },
            'vvix': {
                'spike_threshold': 0.2,  # Daily 100/10/5 at 0.2
                'description': 'VVIX spike = vol expansion precursor'
            }
        }
    
    def analyze(self, ticker, data):
        """
        Main analysis function - returns all Market Memory analysis
        
        TODO: Implement actual breadth data fetching (requires paid data or scraping)
        For now, returns structure with placeholders
        """
        
        result = {
            'breadth': self._analyze_breadth(ticker, data),
            'ratios': self._analyze_ratios(ticker, data),
            'volatility': self._analyze_volatility(data),
            'zone_hit': False,  # Will be True if any memory zone is touched
            'divergence': False  # Intermarket divergence detected
        }
        
        # Check if any zones are hit
        result['zone_hit'] = self._check_zone_hits(result)
        result['divergence'] = self._check_divergences(result)
        
        return result
    
    def _analyze_breadth(self, ticker, data):
        """
        Analyze breadth indicators
        
        TODO: Fetch real breadth data from:
        - Barchart (paid)
        - StockCharts (scraping)
        - Custom calculation from constituent data
        
        For now, returns placeholder structure
        """
        
        breadth_result = {
            'nyse_above_50dma': {
                'value': None,  # TODO: Fetch actual NYSE breadth
                'zone_hit': False,
                'zone_type': None,  # 'red_sell' or 'green_buy'
                'bb_stretched': False  # Bollinger Band %B extreme
            },
            'zweig_thrust': {
                'active': False,
                'start_value': None,
                'current_value': None,
                'days_elapsed': 0,
                'regime_valid': True  # Check against Fed funds rising/falling
            },
            'nymo': {
                'value': None,  # TODO: Calculate McClellan Oscillator
                'zone_hit': False,
                'divergence': False
            },
            'custom_modal': {
                'value': None,  # TODO: Build custom breadth modal
                'leading_break': False  # Breaks before price trendline
            }
        }
        
        # Placeholder - you'll implement actual fetching here
        return breadth_result
    
    def _analyze_ratios(self, ticker, data):
        """
        Analyze intermarket ratios
        
        These can be calculated from yfinance data
        """
        
        ratio_result = {}
        
        # NDX:SPX ratio
        try:
            ndx = yf.Ticker('^NDX').history(period='5y')
            spx = yf.Ticker('^SPX').history(period='5y')
            
            ratio_ndx_spx = ndx['Close'] / spx['Close']
            current_ratio = ratio_ndx_spx.iloc[-1]
            
            ratio_result['ndx_spx'] = {
                'value': float(current_ratio),
                'memory_hit': False,
                'trendline_break': False,  # TODO: Calculate trendline
                'description': 'Tech leadership vs broad market'
            }
        except:
            ratio_result['ndx_spx'] = {
                'value': None,
                'memory_hit': False,
                'error': 'Could not fetch NDX:SPX data'
            }
        
        # IWC:OEX ratio (small cap vs large cap)
        # TODO: Implement similar logic for other ratios
        
        # SPXADP (custom proxy)
        # TODO: Implement
        
        return ratio_result
    
    def _analyze_volatility(self, data):
        """
        Analyze volatility indicators (VIX, VIX9D, VVIX)
        """

        vol_result = {}
        current_vix = None
        vix = None

        # VIX analysis with full memory zones
        try:
            vix = yf.Ticker('^VIX').history(period='2y')  # Longer history for memory analysis
            if vix.empty:
                raise ValueError("VIX history is empty")

            current_vix = vix['Close'].iloc[-1]

            zones = self.volatility_zones['vix']

            # Calculate Bollinger %B on VIX
            vix_percentb = self.calculate_bollinger_percentb(vix['Close'], period=20, std=2)
            bb_stretched = vix_percentb.iloc[-1] > 1.0 or vix_percentb.iloc[-1] < 0.0

            # Find historical VIX memory levels (reversal points)
            vix_memories = self._find_memory_levels(vix['Close'])

            vol_result['vix'] = {
                'value': float(current_vix),
                'extreme': bool(current_vix > zones['red_overbought'] or current_vix < zones['green_oversold']),
                'zone_type': 'red' if current_vix > zones['red_overbought'] else 'green' if current_vix < zones['green_oversold'] else 'neutral',
                'bb_stretched': bool(bb_stretched),
                'percent_b': float(vix_percentb.iloc[-1]) if not np.isnan(vix_percentb.iloc[-1]) else None,
                'memory_levels': vix_memories,
                'near_memory': bool(self._is_near_memory(current_vix, vix_memories)),
                'hurst_divergence': False
            }
        except Exception as e:
            vol_result['vix'] = {
                'value': None,
                'extreme': False,
                'error': f'Could not fetch VIX data: {str(e)}'
            }

        # VIX9D (approximate using VIX - not perfect but free)
        if current_vix is not None:
            vol_result['vix9d'] = {
                'value': float(current_vix * 0.9),
                'extreme': False,
                'note': 'VIX9D approximated from VIX (free alternative)'
            }
        else:
            vol_result['vix9d'] = {
                'value': None,
                'extreme': False,
                'note': 'VIX data unavailable for VIX9D proxy'
            }

        # VVIX (VIX of VIX - volatility of volatility)
        if vix is not None and not vix.empty:
            try:
                # VVIX measures volatility OF the VIX
                # We can approximate by calculating rolling std of VIX
                vvix_approx = vix['Close'].pct_change().rolling(10).std() * np.sqrt(252)
                current_vvix = vvix_approx.iloc[-1]

                # Detect spike: >20% daily move in VIX
                vix_daily_change = vix['Close'].pct_change().iloc[-1]
                spike_detected = abs(vix_daily_change) > 0.2

                vol_result['vvix'] = {
                    'value': float(current_vvix * 100) if not np.isnan(current_vvix) else None,
                    'spike_detected': bool(spike_detected),
                    'vix_daily_change': float(vix_daily_change * 100) if not np.isnan(vix_daily_change) else None,
                    'note': 'VVIX approximated from VIX volatility (free alternative)'
                }
            except Exception as e:
                vol_result['vvix'] = {
                    'value': None,
                    'spike_detected': False,
                    'error': f'VVIX calculation failed: {str(e)}'
                }
        else:
            vol_result['vvix'] = {
                'value': None,
                'spike_detected': False,
                'note': 'VIX data unavailable for VVIX proxy'
            }

        return vol_result

    def _find_memory_levels(self, series, lookback=252, threshold=0.02):
        """
        Find price levels where series has reversed multiple times (memory zones)

        Args:
            series: Price series (e.g., VIX close prices)
            lookback: Days to look back
            threshold: % distance to consider "same level" (2% default)

        Returns:
            List of memory levels with reversal counts
        """
        if len(series) < lookback:
            lookback = len(series)

        data = series.iloc[-lookback:]

        # Find local maxima and minima
        from scipy.signal import find_peaks

        peaks, _ = find_peaks(data.values)
        troughs, _ = find_peaks(-data.values)

        reversal_points = list(data.iloc[peaks].values) + list(data.iloc[troughs].values)

        # Cluster nearby levels
        memories = []
        for point in reversal_points:
            # Check if this point is near an existing memory
            found_cluster = False
            for memory in memories:
                if abs(point - memory['level']) / memory['level'] < threshold:
                    memory['count'] += 1
                    found_cluster = True
                    break

            if not found_cluster:
                memories.append({'level': float(point), 'count': 1})

        # Filter to only significant memories (touched 3+ times)
        significant_memories = [m for m in memories if m['count'] >= 3]

        # Sort by count (most significant first)
        significant_memories.sort(key=lambda x: x['count'], reverse=True)

        return significant_memories[:5]  # Return top 5

    def _is_near_memory(self, current_value, memories, threshold=0.02):
        """Check if current value is near any memory level"""
        for memory in memories:
            if abs(current_value - memory['level']) / memory['level'] < threshold:
                return True
        return False
    
    def _check_zone_hits(self, result):
        """Check if any memory zones are currently touched"""
        
        # Check breadth zones
        for indicator, data in result['breadth'].items():
            if data.get('zone_hit'):
                return True
        
        # Check ratio zones
        for ratio, data in result['ratios'].items():
            if data.get('memory_hit'):
                return True
        
        # Check volatility zones
        for vol_indicator, data in result['volatility'].items():
            if data.get('extreme'):
                return True
        
        return False
    
    def _check_divergences(self, result):
        """Check for intermarket divergences"""
        
        # TODO: Implement divergence detection logic
        # - Price making new highs while breadth declining
        # - VIX cycles mismatched with SPX
        # - Ratio breaks while price holds
        
        return False
    
    def calculate_bollinger_percentb(self, data, period=20, std=2):
        """
        Calculate Bollinger Band %B
        
        Used on breadth oscillators to detect extreme stretches
        """
        
        sma = data.rolling(window=period).mean()
        std_dev = data.rolling(window=period).std()
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        percent_b = (data - lower_band) / (upper_band - lower_band)
        
        return percent_b
    
    def detect_zweig_thrust(self, breadth_data):
        """
        Detect Zweig Breadth Thrust
        
        Condition: % stocks above 50DMA goes from <5% to >90% in 10-15 days
        
        Must check regime - fails in rising rate environments
        """
        
        # TODO: Implement actual detection logic
        # 1. Find periods where value < 5%
        # 2. Check if within next 15 days it exceeds 90%
        # 3. Overlay Fed funds rate direction
        # 4. Return thrust signal with regime validity
        
        return {
            'detected': False,
            'start_date': None,
            'end_date': None,
            'regime_valid': True
        }
