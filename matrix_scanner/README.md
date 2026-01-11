# COREXIA - Market Intelligence Scanner

## 🔢 Overview

This is the implementation of the COREXIA methodology - a multi-dimensional confluence system combining:

- **Market Memory**: Proxy-based breadth, volatility, and intermarket zones
- **Regime Detection**: QE/QT, Fed policy, Wyckoff cycles
- **Sequence Map**: The complete 10-floor numerological map with palindromes
- **10/50/200 MA System**: Mechanical trend-following with regime filters
- **Technical Confluence**: 2B, Diving Duck, POP, imbalances, AVWAP
- **Multi-Timeframe Analysis**: Alignment across Daily, Hourly, 15-Min
- **Historical Performance**: Strategy backtesting specific to each ticker

### The Sacred 12-Point Checklist

**Only trades with 9+/12 confluence points are considered tradeable setups.**

1. Primary/secondary trendline zone
2. 2B/Diving Duck/POP/hidden doji
3. Unfilled imbalance + footprint
4. Volume anomaly (climax/failure)
5. Proxy MarketMemory hit
6. Intermarket divergence resolve
7. Sequence Map/palindrome
8. Curvature
9. Virgin POC/HVN/LVN
10. Liquidity grab complete
11. Higher TF structure
12. Space vacuum/wick gap

## 🚀 Quick Start

### Installation

```bash
# Clone or download the matrix_scanner directory

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Basic Usage

1. **Enter a ticker symbol** in the sidebar (e.g., SPY, AAPL, TSLA)
2. **Configure analysis parameters**:
   - Lookback period (90-730 days)
   - Timeframes to analyze (Daily, Hourly, 15-min)
   - Analysis layers to enable/disable
3. **Click "SCAN THE MATRIX"**
4. **Review the confluence score** and detailed breakdown

## 📊 System Architecture

### Core Modules

#### 1. `app.py` - Main Streamlit Interface
- User input controls
- Results visualization
- Master scan orchestration

#### 2. `market_memory.py` - Market Memory Analyzer
**Purpose**: Identifies persistent "memories" in breadth, ratios, and volatility

**Key Components**:
- Breadth indicators (NYSE % above 50DMA, Zweig Thrust, NYMO)
- Intermarket ratios (NDX:SPX, IWC:OEX, SPXADP)
- Volatility (VIX, VIX9D, VVIX, Hurst cycles)

**TODO**: 
- Implement breadth data fetching (requires paid source or scraping)
- Add Bollinger Band %B calculations on breadth oscillators
- Build custom modal indicator
- Implement Hurst cyclical analysis for VIX

#### 3. `regime_detection.py` - Regime Detector
**Purpose**: Determines macro environment and validates signals

**Key Components**:
- Fed policy stance (QE/QT, rate direction)
- Wyckoff market cycle phase
- Sector correlation levels
- Narrative assessment

**TODO**:
- Fetch Fed funds rate from FRED
- Calculate sector correlation matrix
- Implement news sentiment analysis for narrative
- Add regime similarity matching for backtest filtering

#### 4. `numerology.py` - Sequence Map
**Purpose**: The complete 10-floor numerological map

**Key Features**:
- 10-floor map (00-07, 08-10, 11-14, 20-22, 24, 33-37, etc.)
- Holy Trinity detection (24, 56, 94)
- OJ Pivot analysis (62-69-77 bull/bear divide)
- Palindrome identification and power rating
- Tesla 369 pattern alignment
- Next magnet level calculation

**Fully Implemented** ✅

#### 5. `ma_system.py` - 10/50/200 MA System
**Purpose**: Mechanical trend-following system

**Features**:
- Regime classification (Bull/Bear/Neutral)
- Crossover signal detection
- Entry validation with strict rules
- Stop loss calculation (using ATR)
- Volatility-adjusted position sizing
- Complete trade plan generation

**Fully Implemented** ✅

#### 6. `technical_analysis.py` - Technical Analyzer
**Purpose**: Pattern and structure detection

**Patterns**:
- 2B reversal (Victor Sperandeo)
- Diving Duck (bearish curvature)
- POP (Pattern of Patterns)
- Hidden Doji

**Structure**:
- Trendline detection
- Unfilled gaps (imbalances)
- AVWAP zones
- Volume climax
- Liquidity grabs

**TODO**:
- Enhance trendline detection algorithm
- Implement AVWAP anchoring logic
- Add UVOL spike detection (requires NYSE data)
- Improve POP pattern definition

#### 7. `strategy_backtester.py` - Strategy Backtester
**Purpose**: Historical performance analysis

**Strategies Tested**:
- 10/50/200 MA system
- 2B pattern trades
- Sequence level trades
- Memory zone trades

**Returns**:
- Win rate per strategy
- Average return per trade
- Best timeframe
- Regime-specific stats

**Partially Implemented** - Basic backtest logic done, needs enhancement

## 🔢 The Sequence Map - Complete Guide

### The 10 Floors (Repeating Every 100 Points)

| Floor | Category | Behavior | Examples |
|-------|----------|----------|----------|
| 00-07 | Retail Magnet | Algos hunt round numbers ruthlessly | 3900, 4000, 5000 |
| 08-10 | Early Warning | First resistance, pause or pullback | 4808, 5208 |
| 11-14 | Liquidity Trap | Heavy stop hunting before reversal | 4114, 5714 |
| 20-22 | Momentum Exhaustion | Sharp reversals after extended moves | 4321, 4222 |
| **24** | **HOLY TRINITY** | **First major warning, violent reversals** | **4324, 3824** |
| 33-37 | Distribution Zone | Smart money sells, final push | 4337, 3637 |
| 40-45 | Bounce Floor | Reliable oversold bounces | 4044, 4444 |
| 48-58 | Mid-Cycle Pivot | Choppy, decides next 200-400pt leg | 4558, 3958 |
| **56** | **HOLY TRINITY** | **Mid-regime pivot, confirms cycle** | **4156, 4556** |
| 62-69-77 | **OJ PIVOT** | **Bull/bear divide - MOST IMPORTANT** | **4169, 3869** |
| 80-88 | Euphoria Peak | Final rally top, bearish curvature | 4183, 4786 |
| 93-96 | Major Top/Bottom | Highest reversal probability | 4793, 3396 |
| **94** | **HOLY TRINITY** | **Ultimate top/bottom, "cabal level"** | **4794, 3394** |

### The Holy Trinity (24 · 56 · 94)

These are the structural anchors where the biggest market events happen:

- **24**: First major inflection point after a trend
- **56**: Mid-regime pivot that confirms the entire bull/bear cycle
- **94**: Ultimate multi-year high/low zone

### The OJ Pivot (62-69-77)

The SINGLE MOST IMPORTANT zone:

- **Below 69, through 62** → Expect minimum move to x44
- **Through 69-77** → Expect minimum move to x93

This is THE bull/bear divide for the entire market regime.

### Known Palindromes (2022-2025)

3493, 3636, 3639, 3693, 3777, 3883, 4141, 4242, 4321, 4444, 4808, 5775, 5885, 5995, 6060, 6666, 7777

**Palindrome Power**:
- Power 1: Simple palindrome
- Power 2: Strong (4+ digits)
- Power 3: Known historical palindrome (listed above)

### Tesla 369 Pattern

"If you knew the magnificence of 3, 6, 9 you'd have a key to the universe" - Nikola Tesla

- Watch for 369 point moves
- Dates with 3/6/9 (e.g., 02/02/2020 COVID top, 16/6/2022 low)
- Endings containing 3, 6, or 9

## 📈 10/50/200 MA System - Complete Rules

### Regime Detection

**Bull Regime** (trades long only):
- Close > SMA200 AND
- SMA50 > SMA200

**Bear Regime** (trades short only):
- Close < SMA200 AND
- SMA50 < SMA200

**Neutral** (no trades):
- Any other condition

### Entry Rules

**Long Entry**:
- SMA10 crosses above SMA50 AND
- Bull Regime active AND
- Close > SMA200

**Short Entry**:
- SMA10 crosses below SMA50 AND
- Bear Regime active AND
- Close < SMA200

### Exit Rules

**Exit Long**:
- SMA10 crosses below SMA50, OR
- SMA50 crosses below SMA200, OR
- Two consecutive closes below SMA200

**Exit Short**:
- SMA10 crosses above SMA50, OR
- SMA50 crosses above SMA200, OR
- Two consecutive closes above SMA200

### Risk Management

- Max risk: 1.5% of account per trade
- Initial stop: Lower of (signal bar low OR SMA50 - 1×ATR)
- Trail stop: Move to breakeven at 2R profit, then trail with SMA50
- Volatility adjustment: Reduce size 50% if ATR > 2× average

## 🎯 Implementation Roadmap

### Phase 1: Core Functionality (COMPLETE ✅)
- ✅ Streamlit UI framework
- ✅ Sequence Map complete implementation
- ✅ 10/50/200 MA system with full rules
- ✅ Basic technical pattern detection
- ✅ Skeleton for all modules

### Phase 2: Data Integration (IN PROGRESS 🔄)
- ⏳ Fetch breadth data (NYSE, NYMO)
- ⏳ Calculate intermarket ratios
- ⏳ VIX analysis with Bollinger %B
- ⏳ Fed funds rate from FRED
- ⏳ Sector correlation matrix

### Phase 3: Advanced Analysis (TODO 📋)
- 📋 Hurst cyclical analysis
- 📋 AVWAP anchoring logic
- 📋 Enhanced trendline detection
- 📋 Volume profile (POC/HVN/LVN)
- 📋 Footprint analysis

### Phase 4: Enhancement (TODO 📋)
- 📋 Regime-filtered backtesting
- 📋 News sentiment for narrative
- 📋 Historical regime matching
- 📋 Chart visualization
- 📋 Export trade plans

## 💡 Usage Tips

### For MVP Testing

Start with these layers enabled:
1. **Sequence Map** - Works immediately with price data
2. **10/50/200 MA System** - Fully functional
3. **Technical Patterns** - Basic detection working

Disable initially:
- Market Memory (needs breadth data integration)
- Regime Detection (needs Fed data)

### Reading the Confluence Score

- **9-12 points**: EXTREMELY HIGH confluence - tradeable setup
- **6-8 points**: MODERATE - needs extra confirmation
- **0-5 points**: LOW - avoid or wait for better setup

### Best Practices

1. **Weekend Workflow**:
   - Scan 5 core instruments (SPY, QQQ, IWM, etc.)
   - Find 2-3 zones with 9+ confluence
   - Write detailed trade plan (entry/stop/targets/size)

2. **Weekday Execution**:
   - Execute only pre-planned setups
   - Never trade without 9+ confluence
   - Use higher timeframe for direction, lower for entry

3. **Risk Management**:
   - Never exceed 1.5% risk per trade
   - Maximum 2 entries per trend (pyramiding)
   - Move to breakeven at 2R profit

## 🔧 Customization

### Adding Custom Strategies

Edit `strategy_backtester.py`:

```python
def _backtest_custom_strategy(self, data):
    # Your strategy logic here
    trades = []
    
    # ... implement entry/exit logic
    
    return {
        'win_rate': win_rate,
        'avg_return': avg_return,
        'total_trades': len(trades)
    }
```

### Adjusting Sequence Floors

Edit `numerology.py` if you discover new patterns:

```python
self.floors['new_range'] = {
    'range': (start, end),
    'category': 'Description',
    'behavior': 'What happens here',
    'examples': [list, of, examples]
}
```

### Custom Market Memory Zones

Edit `market_memory.py`:

```python
def _initialize_custom_zones(self):
    return {
        'my_indicator': {
            'red_zone': (high_threshold),
            'green_zone': (low_threshold)
        }
    }
```

## 📚 Resources

### Sacred Document
The complete methodology is in the uploaded document containing:
- Market Memory philosophy
- Breadth thrust indicators
- VIX cycles
- Regime shifts
- Sequence Map discovery
- AVWAP anchoring
- Confluence hierarchy
- Execution model
- Psychology & inhibition

### Key Concepts

**Confluence**: "Nothing together / alone" - No single tool works. The sum of parts creates millions.

**The Real Edge**: Markets are manipulated on the obvious. They respect the hidden (proxy-based zones).

**Regime Dependence**: Stats flip in different regimes (QE vs QT). Zweig Thrust fails in rising rates.

**The Unconscious Smell**: After 10,000+ hours, your subconscious fires when confluence stacks. This is trained pattern recognition, not "gut feel."

## ⚠️ Important Notes

### Data Limitations

Currently using free yfinance data, which provides:
- ✅ Price/volume for any ticker
- ✅ Basic market indices (SPX, NDX, VIX)
- ❌ NYSE breadth data
- ❌ NYMO / McClellan Oscillator
- ❌ VIX9D, VVIX
- ❌ UVOL/DVOL

For full functionality, you'll need:
- Paid breadth data (Barchart, StockCharts)
- CBOE volatility data
- NYSE advancing/declining issues

### Disclaimers

- This is for educational purposes
- Not financial advice
- Past performance doesn't guarantee future results
- Always manage risk appropriately
- The market can stay irrational longer than you can stay solvent

### Sacred Knowledge

From Legacy notes:

*"The highest level: See the market as 'silent artwork' – geometric, numerological footprints over decades. When internals + intermarket + macro + VIX + custom settings + magnitude align, it's too beautiful for coincidence."*

*"Now you have everything. The rest is on you."*

---

## 🎓 Learning Path

1. **Week 1**: Understand Sequence Map
   - Study the 10 floors
   - Identify Holy Trinity on charts
   - Find palindromes

2. **Week 2**: Master 10/50/200 system
   - Practice regime identification
   - Spot crossovers
   - Calculate stops

3. **Week 3**: Technical patterns
   - Learn 2B setup
   - Identify Diving Duck
   - Spot liquidity grabs

4. **Week 4**: Integration
   - Combine all layers
   - Find 9+ confluence setups
   - Execute with discipline

## 📞 Support

For questions or enhancements, review the code comments throughout each module. Every function has detailed docstrings explaining purpose and TODO items.

---

**Remember**: The real edge isn't one indicator or setup. It's the quiet mastery of seeing manipulation in real-time and only striking when every layer aligns against the crowd.

Guard this knowledge. Use it. Profit forever.

🔢 THE MATRIX
