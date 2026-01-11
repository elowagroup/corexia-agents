"""
Technical Analysis Module

Patterns: 2B, Diving Duck, POP, Hidden Doji
Structure: Trendlines, Imbalances, Curvature, AVWAP
Volume: Climax, UVOL, Footprint
"""

import pandas as pd
import numpy as np

class TechnicalAnalyzer:
    """
    Analyzes technical patterns and structure
    
    Key patterns from the document:
    - 2B: Victor Sperandeo's 2B reversal
    - Diving Duck: Bearish curvature pattern
    - POP: Pattern of Patterns
    - Hidden Doji: Subtle indecision candle
    """
    
    def __init__(self):
        pass
    
    def analyze(self, data):
        """
        Main analysis function
        
        Returns all technical analysis components
        """
        
        result = {
            'patterns': self._detect_patterns(data),
            'candles': self._detect_candlestick_patterns(data),
            'bollinger': self._analyze_bollinger(data),
            'structure': self._analyze_structure(data),
            'volume': self._analyze_volume(data),

            # Checklist helpers
            'trendline_hit': False,
            'unfilled_gaps': False,
            'volume_climax': False,
            'curvature': False,
            'balance_zone': False,
            'stophunt_complete': False,
            'vacuum': False,
            'bollinger_squeeze': False
        }
        
        # Populate checklist helpers
        result['trendline_hit'] = result['structure'].get('trendline_touch', False)
        result['unfilled_gaps'] = len(result['structure'].get('gaps', [])) > 0
        result['volume_climax'] = result['volume'].get('climax_detected', False)
        result['curvature'] = result['patterns'].get('diving_duck', False)
        result['stophunt_complete'] = result['volume'].get('liquidity_grab', False)
        result['vacuum'] = result['structure'].get('imbalance_present', False)
        result['balance_zone'] = result['structure'].get('balance_state') in ['in_balance', 'breakout_up', 'breakdown_down']
        result['bollinger_squeeze'] = result['bollinger'].get('squeeze', False)
        
        return result
    
    def _detect_patterns(self, data):
        """
        Detect price action patterns
        
        2B, Diving Duck, POP, Hidden Doji
        """
        
        patterns = {
            '2b': self._detect_2b(data),
            'diving_duck': self._detect_diving_duck(data),
            'pop': self._detect_pop(data),
            'hidden_doji': self._detect_hidden_doji(data)
        }
        
        return patterns
    
    def _detect_2b(self, data):
        """
        2B Pattern Detection (Victor Sperandeo)
        
        Bullish 2B:
        - Price makes new low
        - Fails to continue lower
        - Reverses back above prior low
        
        Bearish 2B:
        - Price makes new high
        - Fails to continue higher
        - Reverses back below prior high
        
        Returns: bool
        """
        
        if len(data) < 10:
            return False
        
        # Look at recent price action
        recent = data.tail(10)
        close = recent['Close'].values
        high = recent['High'].values
        low = recent['Low'].values
        
        # Bearish 2B: New high, failed breakout
        # Find highest high
        max_high_idx = np.argmax(high)
        
        if max_high_idx < len(high) - 3:  # Not too recent
            max_high = high[max_high_idx]
            # Check if tried to break higher but failed
            subsequent_highs = high[max_high_idx + 1:]
            if any(h > max_high * 0.999 for h in subsequent_highs):
                # Tried to break
                if close[-1] < max_high * 0.995:
                    # Failed and reversed
                    return True
        
        # Bullish 2B: New low, failed breakdown
        min_low_idx = np.argmin(low)
        
        if min_low_idx < len(low) - 3:
            min_low = low[min_low_idx]
            subsequent_lows = low[min_low_idx + 1:]
            if any(l < min_low * 1.001 for l in subsequent_lows):
                if close[-1] > min_low * 1.005:
                    return True
        
        return False
    
    def _detect_diving_duck(self, data):
        """
        Diving Duck Pattern
        
        Bearish curvature - price makes rounded top
        Often appears at the 80-88 sequence levels
        
        Characteristics:
        - Slowing upward momentum
        - Rounded top formation
        - Volume declining on rallies
        
        Returns: bool
        """
        
        if len(data) < 20:
            return False
        
        recent = data.tail(20)
        close = recent['Close'].values
        
        # Check for rounded top curvature
        # First half should be trending up
        first_half = close[:10]
        second_half = close[10:]
        
        # Simple check: first half rising, second half falling or flat
        first_trend = first_half[-1] > first_half[0]
        second_trend = second_half[-1] < second_half[0]
        
        # Check for declining volume (if available)
        if 'Volume' in recent.columns:
            vol = recent['Volume'].values
            vol_declining = vol[-5:].mean() < vol[:10].mean()
        else:
            vol_declining = False
        
        # Rounded top = rising then falling
        if first_trend and second_trend:
            return True
        
        return False
    
    def _detect_pop(self, data):
        """
        POP (Pattern of Patterns)
        
        TODO: Implement based on specific POP definition
        This is a meta-pattern that combines multiple signals
        
        Returns: bool
        """
        
        # Placeholder
        return False
    
    def _detect_hidden_doji(self, data):
        """
        Hidden Doji Pattern
        
        Subtle indecision candle - small body, but not obvious doji
        Often appears at inflection points
        
        Characteristics:
        - Small body (close near open)
        - Appears after strong move
        - Wicks on both sides
        
        Returns: bool
        """
        
        if len(data) < 5:
            return False
        
        current = data.iloc[-1]
        
        # Calculate body size
        body_size = abs(current['Close'] - current['Open'])
        total_range = current['High'] - current['Low']
        
        if total_range == 0:
            return False
        
        body_ratio = body_size / total_range
        
        # Hidden doji: body < 20% of range
        if body_ratio < 0.2:
            # Check if after strong move
            prior_move = abs(data.iloc[-5]['Close'] - current['Close'])
            avg_move = data['Close'].diff().abs().tail(20).mean()
            
            if prior_move > avg_move * 1.5:
                return True
        
        return False
    
    def _analyze_structure(self, data):
        """
        Analyze market structure
        
        - Trendlines
        - Imbalances (unfilled gaps)
        - Curvature
        - AVWAP zones
        """
        
        balance = self._analyze_balance_zones(data)
        structure = {
            'trendlines': self._find_trendlines(data),
            'gaps': self._find_gaps(data),
            'avwap_zones': self._calculate_avwap_zones(data),
            'balance_zones': balance.get('zones', []),
            'current_balance': balance.get('current_zone'),
            'balance_state': balance.get('balance_state'),
            'balance_touch_counts': balance.get('touch_counts', {}),
            'balance_touch_rank': balance.get('touch_rank'),

            'trendline_touch': False,
            'imbalance_present': False
        }
        
        # Check if touching trendline
        if structure['trendlines']:
            structure['trendline_touch'] = self._check_trendline_touch(
                data.iloc[-1], structure['trendlines']
            )
        
        # Check for unfilled gaps
        structure['imbalance_present'] = len(structure['gaps']) > 0
        
        return structure

    def _analyze_bollinger(self, data, period=20, std=2, squeeze_quantile=0.15):
        """Analyze Bollinger bands for squeeze and expansion."""
        if len(data) < period + 10:
            return {
                'squeeze': False,
                'bandwidth': None,
                'percent_b': None,
                'note': 'Insufficient data for Bollinger analysis'
            }

        close = data['Close']
        sma = close.rolling(window=period).mean()
        std_dev = close.rolling(window=period).std()

        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        bandwidth = (upper - lower) / sma
        percent_b = (close - lower) / (upper - lower)

        recent_bw = bandwidth.dropna().tail(100)
        threshold = recent_bw.quantile(squeeze_quantile) if not recent_bw.empty else None
        current_bw = bandwidth.iloc[-1] if not bandwidth.empty else None

        squeeze = bool(threshold is not None and current_bw <= threshold)

        return {
            'squeeze': squeeze,
            'bandwidth': float(current_bw) if current_bw is not None and not np.isnan(current_bw) else None,
            'percent_b': float(percent_b.iloc[-1]) if not np.isnan(percent_b.iloc[-1]) else None,
            'upper': float(upper.iloc[-1]) if not np.isnan(upper.iloc[-1]) else None,
            'lower': float(lower.iloc[-1]) if not np.isnan(lower.iloc[-1]) else None,
            'mid': float(sma.iloc[-1]) if not np.isnan(sma.iloc[-1]) else None
        }

    def _detect_candlestick_patterns(self, data):
        """
        Detect key candlestick patterns (simplified).
        """
        if len(data) < 2:
            return {}

        prev = data.iloc[-2]
        curr = data.iloc[-1]

        def body_size(candle):
            return abs(candle['Close'] - candle['Open'])

        def candle_range(candle):
            return candle['High'] - candle['Low']

        curr_body = body_size(curr)
        prev_body = body_size(prev)
        curr_range = candle_range(curr)

        if curr_range == 0:
            return {}

        # Basic candle properties
        curr_is_bull = curr['Close'] > curr['Open']
        prev_is_bull = prev['Close'] > prev['Open']

        upper_wick = curr['High'] - max(curr['Close'], curr['Open'])
        lower_wick = min(curr['Close'], curr['Open']) - curr['Low']

        doji = curr_body <= curr_range * 0.1
        hammer = lower_wick >= curr_body * 2 and upper_wick <= curr_body * 0.5
        shooting_star = upper_wick >= curr_body * 2 and lower_wick <= curr_body * 0.5

        bullish_engulf = (not prev_is_bull) and curr_is_bull and curr['Close'] >= prev['Open'] and curr['Open'] <= prev['Close']
        bearish_engulf = prev_is_bull and (not curr_is_bull) and curr['Open'] >= prev['Close'] and curr['Close'] <= prev['Open']

        return {
            'doji': bool(doji),
            'hammer': bool(hammer),
            'shooting_star': bool(shooting_star),
            'bullish_engulfing': bool(bullish_engulf),
            'bearish_engulfing': bool(bearish_engulf)
        }

    def _analyze_balance_zones(self, data, bins=18):
        """
        Find balance zones using price distribution bins.
        """
        if data is None or data.empty or len(data) < 40:
            return {
                'zones': [],
                'current_zone': None,
                'balance_state': 'none',
                'touch_counts': {},
                'touch_rank': None
            }

        close = data['Close']
        hist, edges = np.histogram(close.values, bins=bins)
        if len(hist) == 0:
            return {
                'zones': [],
                'current_zone': None,
                'balance_state': 'none',
                'touch_counts': {},
                'touch_rank': None
            }

        top_bins = sorted(range(len(hist)), key=lambda i: hist[i], reverse=True)[:3]
        zones = []
        for idx in top_bins:
            low = float(edges[idx])
            high = float(edges[idx + 1])
            if low >= high:
                continue
            zones.append({
                'low': low,
                'high': high,
                'mid': (low + high) / 2,
                'touches': int(hist[idx])
            })

        zones = sorted(zones, key=lambda z: z['touches'], reverse=True)

        wick_zone = self._find_wick_balance_zone(data)
        if wick_zone:
            zones.append(wick_zone)
            zones = sorted(zones, key=lambda z: z['touches'], reverse=True)

        current_price = float(close.iloc[-1])
        current_zone = None
        for zone in zones:
            if zone['low'] <= current_price <= zone['high']:
                current_zone = zone
                break

        balance_state = 'none'
        if current_zone:
            balance_state = 'in_balance'
        elif zones:
            primary = zones[0]
            if current_price > primary['high'] * 1.002:
                balance_state = 'breakout_up'
            elif current_price < primary['low'] * 0.998:
                balance_state = 'breakdown_down'

        touch_counts = {}
        if zones:
            zone = current_zone or zones[0]
            touch_counts = self._count_zone_touches(data, zone['low'], zone['high'])

        touch_rank = None
        if touch_counts.get('all_time') is not None:
            count = touch_counts['all_time']
            if count <= 1:
                touch_rank = 'First touch'
            elif count == 2:
                touch_rank = 'Second touch'
            elif count == 3:
                touch_rank = 'Third touch'
            else:
                touch_rank = 'Fourth+ touch'

        return {
            'zones': zones,
            'current_zone': current_zone,
            'balance_state': balance_state,
            'touch_counts': touch_counts,
            'touch_rank': touch_rank
        }

    def _find_wick_balance_zone(self, data, lookback=252, threshold=0.02):
        """
        Find balance zones by clustering wick highs/lows (trapped buyers/sellers).
        """
        if data is None or data.empty:
            return None
        window = data.tail(lookback)
        highs = window['High'].values
        lows = window['Low'].values

        from scipy.signal import find_peaks

        peaks, _ = find_peaks(highs)
        troughs, _ = find_peaks(-lows)

        points = list(highs[peaks]) + list(lows[troughs])
        if not points:
            return None

        clusters = []
        for point in points:
            matched = False
            for cluster in clusters:
                if abs(point - cluster['level']) / cluster['level'] < threshold:
                    cluster['points'].append(point)
                    cluster['count'] += 1
                    matched = True
                    break
            if not matched:
                clusters.append({'level': float(point), 'points': [point], 'count': 1})

        clusters = sorted(clusters, key=lambda c: c['count'], reverse=True)
        top = clusters[0]
        low = float(min(top['points']))
        high = float(max(top['points']))
        return {
            'low': low,
            'high': high,
            'mid': (low + high) / 2,
            'touches': int(top['count']),
            'source': 'wick_cluster'
        }

    def _count_zone_touches(self, data, low, high):
        """Count how often price touched a balance zone over different windows."""
        def count_in(df):
            return int(((df['High'] >= low) & (df['Low'] <= high)).sum())

        counts = {
            'all_time': count_in(data),
            'year': count_in(data.tail(252)) if len(data) > 10 else None,
            '90d': count_in(data.tail(90)) if len(data) > 10 else None,
            '30d': count_in(data.tail(30)) if len(data) > 10 else None
        }
        return counts
    
    def _find_trendlines(self, data):
        """
        Find significant trendlines
        
        TODO: Implement proper trendline detection
        - Connect swing highs for downtrend
        - Connect swing lows for uptrend
        - Require at least 3 touches
        
        Returns: List of trendline dicts
        """
        
        # Placeholder
        return []
    
    def _find_gaps(self, data):
        """
        Find unfilled gaps (imbalances)
        
        Gap = Previous close to current open has space
        Unfilled = Price hasn't returned to fill the gap
        
        Returns: List of gap dicts with {start, end, filled}
        """
        
        if len(data) < 2:
            return []
        
        gaps = []
        
        for i in range(1, len(data)):
            prev = data.iloc[i-1]
            curr = data.iloc[i]
            
            # Gap up
            if curr['Low'] > prev['High']:
                gap = {
                    'type': 'gap_up',
                    'start': prev['High'],
                    'end': curr['Low'],
                    'date': curr.name,
                    'filled': False
                }
                
                # Check if filled by subsequent price
                subsequent = data.iloc[i:]
                if any(subsequent['Low'] <= prev['High']):
                    gap['filled'] = True
                
                if not gap['filled']:
                    gaps.append(gap)
            
            # Gap down
            elif curr['High'] < prev['Low']:
                gap = {
                    'type': 'gap_down',
                    'start': prev['Low'],
                    'end': curr['High'],
                    'date': curr.name,
                    'filled': False
                }
                
                subsequent = data.iloc[i:]
                if any(subsequent['High'] >= prev['Low']):
                    gap['filled'] = True
                
                if not gap['filled']:
                    gaps.append(gap)
        
        return gaps
    
    def _calculate_avwap_zones(self, data):
        """
        Calculate Anchored VWAP zones
        
        Anchor to:
        - Recent swing lows/highs
        - High volume panic days
        - Major events
        
        Returns: List of AVWAP levels
        """
        
        # TODO: Implement AVWAP calculation
        # Need to identify anchor points first
        
        return []
    
    def _check_trendline_touch(self, current_bar, trendlines):
        """Check if current price is touching a trendline"""
        
        # TODO: Implement
        return False
    
    def _analyze_volume(self, data):
        """
        Analyze volume patterns
        
        - Climax volume
        - UVOL spikes
        - Footprint analysis
        - Liquidity grabs
        """
        
        volume_analysis = {
            'climax_detected': self._detect_volume_climax(data),
            'uvol_spike': self._detect_uvol_spike(data),
            'liquidity_grab': self._detect_liquidity_grab(data),
            
            'avg_volume': data['Volume'].tail(50).mean() if 'Volume' in data else None,
            'current_volume': data.iloc[-1]['Volume'] if 'Volume' in data else None
        }
        
        return volume_analysis
    
    def _detect_volume_climax(self, data):
        """
        Detect volume climax
        
        Characteristics:
        - Extreme volume (2-3x average)
        - Often at turning points
        - Can be buying or selling climax
        
        Returns: bool
        """
        
        if 'Volume' not in data.columns or len(data) < 50:
            return False
        
        current_vol = data.iloc[-1]['Volume']
        avg_vol = data['Volume'].tail(50).mean()
        
        # Climax = volume > 2x average
        if current_vol > avg_vol * 2:
            return True
        
        return False
    
    def _detect_uvol_spike(self, data):
        """
        Detect UVOL (Up Volume) spike
        
        TODO: UVOL requires NYSE up volume data
        Placeholder for now
        
        Returns: bool
        """
        
        # This requires special data feed
        return False
    
    def _detect_liquidity_grab(self, data):
        """
        Detect liquidity grab (stop hunt)
        
        Characteristics:
        - Wick below recent low (or above recent high)
        - Immediate reversal
        - Often on lower volume
        
        Returns: bool
        """
        
        if len(data) < 10:
            return False
        
        recent = data.tail(10)
        current = data.iloc[-1]
        
        # Find recent swing low/high
        recent_low = recent['Low'].min()
        recent_high = recent['High'].max()
        
        # Check for wick below recent low that reversed
        if current['Low'] < recent_low * 0.999:  # Broke below
            if current['Close'] > current['Low'] * 1.002:  # But closed well above
                return True
        
        # Check for wick above recent high that reversed
        if current['High'] > recent_high * 1.001:
            if current['Close'] < current['High'] * 0.998:
                return True
        
        return False
    
    def get_signals(self, data):
        """Simple function to get just the signals"""
        analysis = self.analyze(data)
        
        # Count how many technical signals are active
        pattern_count = sum(analysis['patterns'].values())
        structure_count = int(analysis['structure']['trendline_touch']) + len(analysis['structure']['gaps'])
        volume_count = int(analysis['volume']['climax_detected'])
        candle_count = sum(analysis.get('candles', {}).values())
        bollinger_count = int(analysis.get('bollinger', {}).get('squeeze', False))
        balance_count = 1 if analysis.get('structure', {}).get('balance_state') in ['in_balance', 'breakout_up', 'breakdown_down'] else 0

        return {
            'total_signals': pattern_count + structure_count + volume_count + candle_count + bollinger_count + balance_count,
            'patterns': analysis['patterns'],
            'structure_flags': analysis['structure']['imbalance_present'],
            'balance_state': analysis['structure'].get('balance_state'),
            'bollinger_squeeze': analysis.get('bollinger', {}).get('squeeze', False),
            'candles': analysis.get('candles', {})
        }
