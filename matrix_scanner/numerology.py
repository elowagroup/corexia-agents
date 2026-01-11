"""
Sequence Map - The Complete Numerological Map

The market speaks in numbers every ~100 points
Repeating patterns reflect collective psychology and rhythm

Core Sequence: 08, 11-14, 20-22, 33-37, 44, 50-58, 62-69, 69-77, 83-86, 93-96
Holy Trinity: 24, 56, 94 (structural anchors where biggest events happen)
OJ Pivot: 62-69-77 (bull/bear divide)
"""

import pandas as pd
import numpy as np

class SequenceMap:
    """
    Analyzes price against the Sequence Map numerological levels
    
    The 10 floors repeat every 100 points across all timeframes and instruments
    """
    
    def __init__(self):
        # The complete 10-floor map
        self.floors = {
            '00-07': {
                'range': (0, 7),
                'category': 'Retail Magnet / Psychological Black Hole',
                'behavior': 'Visually perfect. Retail piles in. Algos hunt ruthlessly.',
                'examples': [3900, 4000, 4500, 5000, 6000]
            },
            '08-10': {
                'range': (8, 10),
                'category': 'Minor stall / early warning',
                'behavior': 'First subtle resistance in upmoves. Pause or small pullback.',
                'examples': [4808, 4008, 5208]
            },
            '11-14': {
                'range': (11, 14),
                'category': 'Liquidity trap zone',
                'behavior': 'Heavy stop hunting. Wicks frequently run here before reversing.',
                'examples': [4814, 4114, 5714]
            },
            '20-22': {
                'range': (20, 22),
                'category': 'Momentum exhaustion',
                'behavior': 'Common area for sharp reversals after extended moves.',
                'examples': [4321, 4322, 4222, 5220]
            },
            '24': {
                'range': (24, 24),
                'category': 'HOLY TRINITY - First major warning',
                'behavior': 'Frequently exact turning point. Violent wick reversals.',
                'examples': [4324, 3824, 5224],
                'holy_level': True
            },
            '33-37': {
                'range': (33, 37),
                'category': 'Distribution zone',
                'behavior': 'Smart money sells into strength. Final push before drops.',
                'examples': [4337, 3633, 3637]
            },
            '40-45': {
                'range': (40, 45),
                'category': 'Minor support / bounce floor',
                'behavior': 'Reliable oversold bounce zone. Temporary bottoms.',
                'examples': [4044, 3844, 4444]
            },
            '48-58': {
                'range': (48, 58),
                'category': 'Mid-cycle pivot',
                'behavior': 'Choppy consolidation. Decides next 200-400pt leg.',
                'examples': [4558, 3950, 3958]
            },
            '56': {
                'range': (56, 56),
                'category': 'HOLY TRINITY - Mid-regime pivot',
                'behavior': 'Break or hold confirms entire bull/bear cycle.',
                'examples': [4156, 4556, 4756],
                'holy_level': True
            },
            '62-69-77': {
                'range': (62, 77),
                'category': 'THE OJ PIVOT (Bull/Bear Divide)',
                'behavior': 'Most important zone. Below 69 through 62 = min 44 coming. Through 69-77 = min 93.',
                'examples': [4169, 3869, 3762, 3769, 4369, 4769, 4777],
                'oj_pivot': True
            },
            '80-88': {
                'range': (80, 88),
                'category': 'Sentiment Exhaustion / Upper Boundary',
                'behavior': 'Euphoria peaks. Bearish curvature almost guaranteed. Final rally top.',
                'examples': [4183, 4186, 4783, 4786]
            },
            '93-96': {
                'range': (93, 96),
                'category': 'Major top / capitulation',
                'behavior': 'Highest probability reversal zone. Smart money flips here.',
                'examples': [4793, 4796, 4193, 4196, 3393, 3396]
            },
            '94': {
                'range': (94, 94),
                'category': 'HOLY TRINITY - Ultimate top/bottom',
                'behavior': 'The "cabal" level. Highest probability for multi-year highs/lows.',
                'examples': [4794, 3394, 4194, 5594],
                'holy_level': True
            }
        }
        
        # Known palindromes that worked 2022-2025
        self.known_palindromes = [
            3493, 3636, 3639, 3693, 3777, 3883,
            4141, 4242, 4321, 4444, 4808,
            5775, 5885, 5995,
            6060, 6666, 7777
        ]
        
        # Tesla 369 pattern
        self.tesla_369 = [3, 6, 9]
    
    def analyze(self, price):
        """
        Main analysis function
        
        Returns:
        {
            'current_price': float,
            'current_floor': str (range),
            'floor_type': str (category),
            'floor_behavior': str,
            'is_holy_trinity': bool,
            'is_oj_pivot': bool,
            'is_palindrome': bool,
            'palindrome_power': int (0-3, 3 = very powerful),
            'next_magnets': [list of next sequence levels],
            'distance_to_holy': {24: x, 56: y, 94: z},
            'tesla_369_alignment': bool,
            'sequence_score': int (0-10)
        }
        """
        
        # Extract the last two digits
        last_two_digits = int(price) % 100
        
        # Identify which floor we're on
        floor_info = self._identify_floor(last_two_digits)
        
        # Check if palindrome
        is_palindrome, palindrome_power = self._check_palindrome(price)
        
        # Find next magnets (important sequence levels above/below)
        next_magnets = self._find_next_magnets(price)
        
        # Distance to Holy Trinity levels
        distance_to_holy = self._distance_to_holy_trinity(price)
        
        # Check Tesla 369 alignment
        tesla_369_alignment = self._check_369_alignment(price, last_two_digits)
        
        # Calculate sequence score (0-10)
        sequence_score = self._calculate_sequence_score(
            floor_info,
            is_palindrome,
            palindrome_power,
            distance_to_holy
        )
        
        return {
            'current_price': price,
            'current_floor': floor_info['range_name'],
            'floor_type': floor_info['category'],
            'floor_behavior': floor_info['behavior'],
            'is_holy_trinity': floor_info.get('holy_level', False),
            'is_oj_pivot': floor_info.get('oj_pivot', False),
            'is_palindrome': is_palindrome,
            'palindrome_power': palindrome_power,
            'next_magnets': next_magnets,
            'distance_to_holy': distance_to_holy,
            'tesla_369_alignment': tesla_369_alignment,
            'sequence_score': sequence_score
        }
    
    def _identify_floor(self, last_two_digits):
        """Identify which floor the price is on"""
        
        for floor_name, floor_data in self.floors.items():
            floor_range = floor_data['range']
            
            if len(floor_range) == 2:
                low, high = floor_range
                if low <= last_two_digits <= high:
                    return {
                        'range_name': floor_name,
                        'category': floor_data['category'],
                        'behavior': floor_data['behavior'],
                        'holy_level': floor_data.get('holy_level', False),
                        'oj_pivot': floor_data.get('oj_pivot', False)
                    }
        
        # Default if not found
        return {
            'range_name': 'Unknown',
            'category': 'Unknown',
            'behavior': 'No specific pattern identified',
            'holy_level': False,
            'oj_pivot': False
        }
    
    def _check_palindrome(self, price):
        """
        Check if price is a palindrome
        
        Returns:
            (is_palindrome, power)
            power: 0 = not palindrome, 1 = weak, 2 = strong, 3 = very powerful
        """
        
        price_str = str(int(price))
        
        # Check if palindrome
        is_palindrome = price_str == price_str[::-1]
        
        if not is_palindrome:
            return False, 0
        
        # Check if it's a known powerful palindrome
        if int(price) in self.known_palindromes:
            return True, 3
        
        # Length-based power
        # Longer palindromes are rarer and more powerful
        length = len(price_str)
        if length >= 4:
            return True, 2
        else:
            return True, 1
    
    def _find_next_magnets(self, current_price):
        """
        Find next important sequence levels (magnets)
        
        Priority:
        1. Holy Trinity (24, 56, 94)
        2. OJ Pivot (62-69-77 range)
        3. Known palindromes
        4. Major floors (00, 20, 40, 80)
        """
        
        magnets = []
        
        # Get current 100-point bucket
        current_hundred = int(current_price / 100) * 100
        
        # Check levels in current and next 100-point ranges
        for base in [current_hundred - 100, current_hundred, current_hundred + 100]:
            # Holy Trinity
            for holy in [24, 56, 94]:
                level = base + holy
                if abs(level - current_price) < 100 and level != int(current_price):
                    magnets.append(level)
            
            # OJ Pivot range
            for oj in [62, 69, 77]:
                level = base + oj
                if abs(level - current_price) < 100 and level != int(current_price):
                    magnets.append(level)
            
            # Round numbers
            for round_num in [0, 50]:
                level = base + round_num
                if abs(level - current_price) < 100 and level != int(current_price):
                    magnets.append(level)
        
        # Check nearby known palindromes
        for palindrome in self.known_palindromes:
            if abs(palindrome - current_price) < 200:
                magnets.append(palindrome)
        
        # Sort by distance and return closest 5
        magnets = sorted(set(magnets), key=lambda x: abs(x - current_price))
        
        return magnets[:5]
    
    def _distance_to_holy_trinity(self, current_price):
        """Calculate distance to each Holy Trinity level"""
        
        distances = {}
        
        # Get current 100-point bucket
        current_hundred = int(current_price / 100) * 100
        
        # Check current and adjacent buckets
        for base in [current_hundred - 100, current_hundred, current_hundred + 100]:
            for holy in [24, 56, 94]:
                level = base + holy
                distance = level - current_price
                
                # Keep only if closer than existing
                if holy not in distances or abs(distance) < abs(distances[holy]['distance']):
                    distances[holy] = {
                        'level': level,
                        'distance': distance,
                        'points_away': abs(distance)
                    }
        
        return distances
    
    def _check_369_alignment(self, price, last_two_digits):
        """
        Check for Tesla 369 pattern alignment
        
        Nikola Tesla: "If you knew the magnificence of 3, 6, 9 you'd have a key to the universe"
        
        Applied to markets:
        - 369 point moves
        - Dates with 3/6/9
        - Endings with 3/6/9
        """
        
        # Check if last two digits contain 3, 6, or 9
        digit_alignment = any(str(d) in str(last_two_digits) for d in [3, 6, 9])
        
        # Could also check:
        # - Is this a 333, 666, 999 point move from a major level?
        # - Is today the 3rd, 6th, 9th, etc day of month?
        
        return digit_alignment
    
    def _calculate_sequence_score(self, floor_info, is_palindrome, palindrome_power, distance_to_holy):
        """
        Calculate overall sequence significance score (0-10)
        
        Higher score = stronger numerological confluence
        """
        
        score = 0
        
        # Holy Trinity level = automatic high score
        if floor_info.get('holy_level'):
            score += 5
        
        # OJ Pivot = significant
        if floor_info.get('oj_pivot'):
            score += 3
        
        # Palindrome power
        score += palindrome_power
        
        # Close to Holy Trinity
        min_distance = min(d['points_away'] for d in distance_to_holy.values())
        if min_distance < 10:
            score += 2
        elif min_distance < 25:
            score += 1
        
        # Major floor categories
        if floor_info['category'] in ['Major top / capitulation', 'Distribution zone', 'Momentum exhaustion']:
            score += 1
        
        return min(10, score)
    
    def interpret_oj_pivot(self, price):
        """
        Special interpretation for OJ Pivot (62-69-77)
        
        Rules from document:
        - Below 69 through 62 → minimum target is 44
        - Through 69-77 → minimum target is 93
        
        This is THE bull/bear divide for entire regime
        """
        
        last_two = int(price) % 100
        current_hundred = int(price / 100) * 100
        
        if 62 <= last_two <= 77:
            position = "Inside OJ Pivot"
            
            if last_two < 69:
                bias = "Bearish - below 69, expect move to x44"
                target = current_hundred + 44
            else:
                bias = "Bullish - above 69, expect move to x93"
                target = current_hundred + 93
            
            return {
                'position': position,
                'bias': bias,
                'target': target,
                'critical_level': current_hundred + 69
            }
        
        return None
    
    def generate_commentary(self, analysis):
        """
        Generate human-readable commentary on the numerological setup
        """
        
        commentary = []
        
        # Opening statement
        commentary.append(f"Price at {analysis['current_price']:.2f}")
        commentary.append(f"Currently on the {analysis['current_floor']} floor")
        commentary.append(f"Category: {analysis['floor_type']}")
        
        # Special levels
        if analysis['is_holy_trinity']:
            commentary.append("🔥 AT HOLY TRINITY LEVEL - Maximum significance")
        
        if analysis['is_oj_pivot']:
            commentary.append("⚡ INSIDE OJ PIVOT (62-69-77) - The bull/bear divide")
        
        if analysis['is_palindrome']:
            power_text = {1: "weak", 2: "strong", 3: "VERY POWERFUL"}
            commentary.append(f"🔢 PALINDROME DETECTED - {power_text[analysis['palindrome_power']].upper()}")
        
        # Next magnets
        if analysis['next_magnets']:
            magnet_str = ", ".join(map(str, analysis['next_magnets'][:3]))
            commentary.append(f"Next magnets: {magnet_str}")
        
        # Sequence score
        if analysis['sequence_score'] >= 8:
            commentary.append("✅ EXTREMELY STRONG numerological confluence")
        elif analysis['sequence_score'] >= 5:
            commentary.append("⚠️ MODERATE numerological support")
        else:
            commentary.append("No major numerological significance at this level")
        
        return "\n".join(commentary)
