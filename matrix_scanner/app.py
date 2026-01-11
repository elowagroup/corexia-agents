"""
COREXIA MARKET INTELLIGENCE
Institutional-grade confluence and market memory engine
"""

import os
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# Import all analysis modules
from market_memory import MarketMemoryAnalyzer
from regime_detection import RegimeDetector
from numerology import SequenceMap
from ma_system import MovingAverageSystem
from technical_analysis import TechnicalAnalyzer
from strategy_backtester import StrategyBacktester
from event_feeds import (
    get_alpha_vantage_key,
    fetch_alpha_vantage_news,
    fetch_alpha_vantage_market_news,
    fetch_alpha_vantage_macro,
    fetch_yahoo_rss_news,
    fetch_sec_filings,
)
from scanner_universe import get_universe_symbols

# Page config
st.set_page_config(
    page_title="COREXIA",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
:root {
    --bg: #0b0f14;
    --panel: #121722;
    --panel-2: #0f141c;
    --text: #e6e8ed;
    --muted: #93a0b2;
    --accent: #f45b69;
    --accent-2: #3ddc97;
    --line: #1e2633;
    --warn: #f6c343;
}
html, body, [class*="css"]  {
    font-family: 'Manrope', system-ui, sans-serif;
    color: var(--text);
}
.stApp {
    background: radial-gradient(circle at 15% 10%, #141b26 0%, #0b0f14 60%);
}
.corexia-title {
    font-family: 'Space Grotesk', system-ui, sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin: 0.2rem 0 0.4rem 0;
}
.corexia-tagline {
    color: var(--muted);
    font-size: 1.05rem;
    margin-bottom: 1.6rem;
}
.macro-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 12px;
}
.macro-card {
    background: linear-gradient(145deg, #121722 0%, #0f141c 100%);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px 16px;
    text-decoration: none;
    color: var(--text);
    display: block;
}
.macro-card:hover {
    border-color: #2c3a4f;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
}
.macro-title {
    font-weight: 600;
    letter-spacing: 0.02em;
}
.macro-metric {
    font-size: 1.4rem;
    font-weight: 700;
    margin-top: 6px;
}
.pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.75rem;
    background: #1c2432;
    color: var(--muted);
}
.pill-accent {
    background: rgba(244, 91, 105, 0.18);
    color: #ff9aa4;
}
.pill-green {
    background: rgba(61, 220, 151, 0.18);
    color: #7ff1bf;
}
.state-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    margin-right: 6px;
}
.state-bull { background: #3ddc97; }
.state-bear { background: #f45b69; }
.state-chop { background: #f6c343; }
.state-label {
    font-size: 0.8rem;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
}
.section-title {
    font-family: 'Space Grotesk', system-ui, sans-serif;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 0.4rem;
}
.score-card {
    background: #121722;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 18px;
}
.score-main {
    font-size: 2rem;
    font-weight: 700;
}
.subtle {
    color: var(--muted);
}
.info-card {
    background: #101620;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px 16px;
}
</style>
""", unsafe_allow_html=True)

MACRO_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "VIX"]
TIMEFRAME_OPTIONS = {
    "1W": {"label": "Weekly (1W)", "interval": "1wk", "max_days": 7300, "resample": None},
    "1D": {"label": "Daily (1D)", "interval": "1d", "max_days": 7300, "resample": None},
    "4H": {"label": "4-Hour (4H)", "interval": "60m", "max_days": 730, "resample": "4H"},
    "90M": {"label": "90-Minute (90M)", "interval": "90m", "max_days": 120, "resample": None},
    "30M": {"label": "30-Minute (30M)", "interval": "30m", "max_days": 60, "resample": None},
}

SCAN_SYMBOL_LIMIT = 500

HISTORICAL_EVENTS = [
    {"date": "2008-09-15", "label": "Lehman collapse"},
    {"date": "2011-08-08", "label": "US credit downgrade"},
    {"date": "2020-02-24", "label": "COVID shock begins"},
    {"date": "2020-03-23", "label": "COVID bottom"},
    {"date": "2022-06-15", "label": "75bps Fed hike"},
    {"date": "2023-03-10", "label": "Regional bank stress"},
]

def init_session_state():
    if "active_symbol" not in st.session_state:
        st.session_state.active_symbol = "SPY"
    if "active_view" not in st.session_state:
        st.session_state.active_view = "macro"
    if "cache_bust" not in st.session_state:
        st.session_state.cache_bust = 0

def apply_query_params():
    params = st.query_params
    symbol = params.get("symbol")
    view = params.get("view")
    if isinstance(symbol, list):
        symbol = symbol[0] if symbol else None
    if isinstance(view, list):
        view = view[0] if view else None
    if symbol:
        st.session_state.active_symbol = symbol.upper()
    if view:
        st.session_state.active_view = view

def sidebar_controls():
    with st.sidebar:
        st.markdown("**COREXIA CONTROL DECK**")
        ticker = st.text_input("Focus Ticker", st.session_state.active_symbol).upper().strip()
        if ticker:
            st.session_state.active_symbol = ticker
            st.session_state.active_view = "symbol"

        if st.button("Refresh Data", use_container_width=True):
            st.session_state.cache_bust += 1

    return {
        "lookback_days": 7300,
        "primary_tf": "1D",
        "timeframes": {tf: (tf in ["1W", "1D", "4H", "90M", "30M"]) for tf in TIMEFRAME_OPTIONS.keys()},
        "layers": {
            "market_memory": True,
            "regime": True,
            "sequence": True,
            "ma_system": True,
            "technical": True,
            "backtest": False
        },
        "cache_bust": st.session_state.cache_bust
    }

def main():
    init_session_state()
    apply_query_params()

    st.markdown('<div class="corexia-title">COREXIA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="corexia-tagline">Macro intelligence, confluence discipline, human clarity.</div>',
        unsafe_allow_html=True
    )

    settings = sidebar_controls()

    macro_snapshot = cached_macro_snapshot(
        settings["lookback_days"],
        settings["layers"],
        settings["cache_bust"]
    )

    render_macro_header(macro_snapshot)
    st.divider()

    if st.session_state.active_view == "macro":
        render_macro_overview(macro_snapshot, settings)
        st.divider()
        render_confluence_scanner(settings)
    elif st.session_state.active_view == "philosophy":
        render_philosophy_page()
    else:
        try:
            result = cached_scan(
                st.session_state.active_symbol,
                settings["lookback_days"],
                settings["timeframes"],
                settings["layers"],
                settings["primary_tf"],
                settings["cache_bust"]
            )
            render_symbol_analysis(result, settings)
        except Exception as exc:
            st.error(f"Scan failed: {exc}")
def run_corexia_scan(ticker, lookback_days, timeframes, layers, primary_tf="1D", fast=False):
    """Master function that orchestrates the COREXIA scan."""
    memory_analyzer = MarketMemoryAnalyzer() if layers.get('market_memory') else None
    regime_detector = RegimeDetector() if layers.get('regime') else None
    sequence_analyzer = SequenceMap() if layers.get('sequence') else None
    ma_system = MovingAverageSystem() if layers.get('ma_system') else None
    technical_analyzer = TechnicalAnalyzer() if layers.get('technical') else None
    backtester = StrategyBacktester() if layers.get('backtest') else None

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    data_symbol = "^VIX" if ticker.upper() == "VIX" else ticker
    stock = yf.Ticker(data_symbol)
    data_daily = stock.history(start=start_date, end=end_date, interval='1d')

    if data_daily is None or data_daily.empty:
        raise ValueError(f"No price data returned for {ticker}")

    data_daily = data_daily.tz_localize(None) if hasattr(data_daily.index, 'tz') else data_daily
    current_price = float(data_daily['Close'].iloc[-1])

    result = {
        'ticker': ticker,
        'current_price': current_price,
        'scan_time': datetime.now(),
        'confluence_score': 0,
        'weighted_score': 0,
        'weighted_max': 0,
        'tradeable': False,
        'market_friction': 'Unknown',
        'friction_signal': '',
        'risk_level': 'Unknown',  # Backward compatibility
        'risk_signal': '',  # Backward compatibility
        'headline_signal': '',
        'checklist': {},
        'layers': {},
        'data': {
            'daily': data_daily,
            'timeframes': {}
        }
    }

    if layers.get('market_memory') and memory_analyzer:
        result['layers']['market_memory'] = memory_analyzer.analyze(ticker, data_daily)

    if layers.get('regime') and regime_detector:
        result['layers']['regime'] = regime_detector.detect(data_daily)

    if layers.get('sequence') and sequence_analyzer:
        result['layers']['sequence'] = sequence_analyzer.analyze(current_price)

    if layers.get('ma_system') and ma_system:
        result['layers']['ma_system'] = ma_system.analyze(data_daily)

    if layers.get('technical') and technical_analyzer:
        result['layers']['technical'] = technical_analyzer.analyze(data_daily)

    result['layers']['timeframes'] = {}
    active_timeframes = [tf for tf, enabled in timeframes.items() if enabled]
    for tf in active_timeframes:
        tf_data = fetch_timeframe_data(stock, tf, lookback_days)
        if tf_data is None or tf_data.empty:
            result['layers']['timeframes'][tf] = {
                'sequence': None,
                'ma_regime': None,
                'technical': None,
                'error': 'No data for timeframe'
            }
            continue

        result['data']['timeframes'][tf] = tf_data
        result['layers']['timeframes'][tf] = {
            'sequence': sequence_analyzer.analyze(tf_data['Close'].iloc[-1]) if sequence_analyzer else None,
            'ma_regime': ma_system.get_regime(tf_data) if ma_system else None,
            'technical': technical_analyzer.get_signals(tf_data) if technical_analyzer else None
        }

    if primary_tf in result['data']['timeframes']:
        result['data']['primary'] = result['data']['timeframes'][primary_tf]
    else:
        result['data']['primary'] = data_daily

    if layers.get('backtest') and backtester and not fast:
        result['layers']['backtest'] = backtester.run_all_strategies(ticker, data_daily)

    result['checklist'] = calculate_checklist(result['layers'])
    weighted_score, weighted_max, normalized = calculate_weighted_score(result['checklist'])
    result['weighted_score'] = weighted_score
    result['weighted_max'] = weighted_max
    result['confluence_score'] = normalized
    result['tradeable'] = normalized >= 9

    # Compute horizon states first (needed by determine_primary_state)
    states = compute_state_by_horizon(result['layers'])
    result['market_states'] = states

    # Use new state classification system
    primary_state, direction_bias = determine_primary_state(result)
    result['market_state'] = primary_state
    result['direction_bias'] = direction_bias

    # Assess market friction (replaces old risk assessment)
    friction_level, friction_signal = assess_market_friction(result)
    result['market_friction'] = friction_level
    result['friction_signal'] = friction_signal

    # Backward compatibility - keep old keys as aliases
    result['risk_level'] = friction_level
    result['risk_signal'] = friction_signal

    result['headline_signal'] = build_headline_summary(result)

    return result

def fetch_timeframe_data(stock, timeframe, lookback_days):
    """Fetch data for specific timeframe with provider limits."""
    cfg = TIMEFRAME_OPTIONS.get(timeframe)
    if not cfg:
        return None

    end_date = datetime.now()
    max_days = cfg["max_days"]
    start_date = end_date - timedelta(days=min(lookback_days, max_days))

    data = stock.history(start=start_date, end=end_date, interval=cfg["interval"])
    if data is None or data.empty:
        return data

    data = data.tz_localize(None) if hasattr(data.index, 'tz') else data
    if cfg.get("resample"):
        data = (
            data.resample(cfg["resample"])
            .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
            .dropna()
        )

    return data

def resolve_alpha_key():
    """Resolve Alpha Vantage key from Streamlit secrets or environment."""
    key = None
    try:
        key = st.secrets.get("ALPHAVANTAGE_API_KEY")
    except Exception:
        key = None
    return key or get_alpha_vantage_key()

@st.cache_data(ttl=900, show_spinner=False)
def cached_alpha_news(ticker, api_key):
    return fetch_alpha_vantage_news(ticker, api_key, limit=20)

@st.cache_data(ttl=900, show_spinner=False)
def cached_market_news(api_key):
    return fetch_alpha_vantage_market_news(api_key, limit=15)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_macro_events(api_key):
    return fetch_alpha_vantage_macro(api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_sec_filings(ticker):
    return fetch_sec_filings(ticker, limit=10)

@st.cache_data(ttl=1800, show_spinner=False)
def cached_rss_news(ticker):
    return fetch_yahoo_rss_news(ticker, limit=10)

@st.cache_data(ttl=900, show_spinner=False)
def cached_scan(ticker, lookback_days, timeframes, layers, primary_tf, cache_bust):
    return run_corexia_scan(
        ticker=ticker,
        lookback_days=lookback_days,
        timeframes=timeframes,
        layers=layers,
        primary_tf=primary_tf,
        fast=False
    )

@st.cache_data(ttl=900, show_spinner=False)
def cached_macro_snapshot(lookback_days, layers, cache_bust):
    snapshot = {}
    macro_layers = dict(layers)
    macro_layers['backtest'] = False
    for symbol in MACRO_SYMBOLS:
        try:
            snapshot[symbol] = run_corexia_scan(
                ticker=symbol,
                lookback_days=lookback_days,
                timeframes={"1W": True, "1D": True, "4H": True, "90M": True},
                layers=macro_layers,
                primary_tf="1D",
                fast=True
            )
        except Exception:
            snapshot[symbol] = {
                'confluence_score': 0,
                'risk_level': 'Unknown',
                'headline_signal': 'Data unavailable.'
            }
    snapshot['COMBINED'] = build_combined_macro(snapshot)
    return snapshot

@st.cache_data(ttl=21600, show_spinner=False)
def cached_top_confluence(index_name, cache_bust):
    universe = get_universe_symbols(index_name)
    total = len(universe)
    if not universe:
        return {"scanned": 0, "total": 0, "bullish": [], "bearish": []}

    scan_layers = {
        "market_memory": True,
        "regime": True,
        "sequence": True,
        "ma_system": True,
        "technical": True,
        "backtest": False
    }
    scan_timeframes = {"1W": True, "1D": True, "4H": True, "90M": True, "30M": True}
    scan_days = 7300

    bullish = []
    bearish = []
    for symbol in universe[:SCAN_SYMBOL_LIMIT]:
        try:
            scan = run_corexia_scan(
                ticker=symbol,
                lookback_days=scan_days,
                timeframes=scan_timeframes,
                layers=scan_layers,
                primary_tf="1D",
                fast=True
            )
        except Exception:
            continue

        mid_state = scan.get("market_states", {}).get("mid")
        record = {
            "Symbol": symbol,
            "Confluence": scan.get("confluence_score", 0),
            "Friction": scan.get("market_friction", "Unknown")
        }
        if mid_state == "Bullish":
            bullish.append(record)
        elif mid_state == "Bearish":
            bearish.append(record)

    bullish = sorted(bullish, key=lambda x: x["Confluence"], reverse=True)[:5]
    bearish = sorted(bearish, key=lambda x: x["Confluence"], reverse=True)[:5]
    return {"scanned": min(total, SCAN_SYMBOL_LIMIT), "total": total, "bullish": bullish, "bearish": bearish}

def build_price_chart(data, balance_zone=None, events=None, signal_markers=None, title=None):
    """Build a price chart with MA + Bollinger overlays and balance zones."""
    df = data.copy()
    df['SMA10'] = df['Close'].rolling(window=10).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    bb_mid = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_UPPER'] = bb_mid + (bb_std * 2)
    df['BB_LOWER'] = bb_mid - (bb_std * 2)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA10'], name='SMA10', line=dict(color='#39d98a')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name='SMA50', line=dict(color='#f6c343')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name='SMA200', line=dict(color='#f45b69')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_UPPER'], name='BB Upper', line=dict(color='#4f5d75', width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_LOWER'], name='BB Lower', line=dict(color='#4f5d75', width=1), fill='tonexty', fillcolor='rgba(79, 93, 117, 0.15)'))

    if balance_zone:
        low = balance_zone.get('low')
        high = balance_zone.get('high')
        mid = balance_zone.get('mid')
        if low is not None and high is not None:
            fig.add_hrect(
                y0=low,
                y1=high,
                line_width=0,
                fillcolor='rgba(61, 220, 151, 0.12)'
            )
            fig.add_hline(y=low, line_width=1, line_dash="dot", line_color="rgba(61, 220, 151, 0.8)")
            fig.add_hline(y=high, line_width=1, line_dash="dot", line_color="rgba(61, 220, 151, 0.8)")
        if mid is not None:
            fig.add_hline(y=mid, line_width=1, line_dash="dash", line_color="rgba(246, 195, 67, 0.9)")

    if events:
        for event in events:
            event_date = event.get("date")
            if event_date is None:
                continue
            fig.add_vline(x=event_date, line_width=1, line_dash="dot", line_color="rgba(244, 91, 105, 0.4)")

    if signal_markers:
        fig.add_trace(go.Scatter(
            x=[m["date"] for m in signal_markers],
            y=[m["price"] for m in signal_markers],
            mode="markers",
            marker=dict(size=7, color="#f6c343", symbol="circle"),
            name="Signals",
            hovertext=[m["hover"] for m in signal_markers],
            hoverinfo="text"
        ))

    fig.update_layout(
        height=460,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_rangeslider_visible=False,
        title=title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def filter_chart_data(data, range_key):
    if data is None or data.empty:
        return data
    end = data.index.max()
    if range_key == "6M":
        start = end - pd.Timedelta(days=183)
        return data.loc[data.index >= start]
    if range_key == "1Y":
        start = end - pd.Timedelta(days=365)
        return data.loc[data.index >= start]
    if range_key == "5Y":
        start = end - pd.Timedelta(days=365 * 5)
        return data.loc[data.index >= start]
    if range_key == "YTD":
        year_start = pd.Timestamp(end.year, 1, 1)
        return data.loc[data.index >= year_start]
    return data

def build_market_memory_trace(result, max_events=30):
    """
    Build multi-timeframe trace of high-confluence states and their outcomes.

    This is NOT a signal log. It is a behavioral record of similar market states.

    Returns: DataFrame with columns:
    - Date, Timeframe, Signal, Context
    - Delta %, Peak %, Trough %
    - Resolution Type (NEW)
    """
    events = []
    data_sets = dict(result.get("data", {}).get("timeframes", {}))
    if "1D" not in data_sets and result.get("data", {}).get("daily") is not None:
        data_sets["1D"] = result.get("data", {}).get("daily")

    for tf, data in data_sets.items():
        if data is None or data.empty:
            continue
        events.extend(build_timeline_for_df(data, tf))

    if not events:
        return pd.DataFrame(columns=[
            "Date", "Timeframe", "Signal", "Context",
            "Delta %", "Peak %", "Trough %", "Resolution Type"
        ])

    # Classify resolution type for each event
    for event in events:
        delta = event.get("Delta %", 0)
        peak = event.get("Peak %", 0)
        trough = event.get("Trough %", 0)

        # Classification logic
        if abs(delta) < 2 and abs(peak) < 3 and abs(trough) < 3:
            resolution = "Chop / Fade"
        elif delta > 0 and peak > abs(trough) * 2:
            resolution = "Trend Continuation"
        elif delta < 0 and abs(trough) > peak * 2:
            resolution = "Trend Continuation"
        elif abs(delta) < abs(peak - trough) / 2:
            resolution = "Mean Reversion"
        else:
            resolution = "Mixed"

        event["Resolution Type"] = resolution

    events = sorted(events, key=lambda x: x["Date"], reverse=True)[:max_events]
    return pd.DataFrame(events)


def build_signal_timeline(result, max_events=30):
    """Legacy wrapper for build_market_memory_trace(). Use build_market_memory_trace() for new code."""
    return build_market_memory_trace(result, max_events)

def build_timeline_for_df(data, tf):
    df = data.copy()
    df['SMA10'] = df['Close'].rolling(window=10).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    tech = TechnicalAnalyzer()
    sequence = SequenceMap()
    balance = tech._analyze_balance_zones(df)
    zone = balance.get('current_zone') or (balance.get('zones') or [None])[0]

    bb_mid = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    bb_width = (bb_mid + bb_std * 2 - (bb_mid - bb_std * 2)) / bb_mid
    bb_threshold = bb_width.dropna().quantile(0.2) if not bb_width.dropna().empty else None

    events = []
    max_signals = 6
    threshold = max_signals // 2

    for i in range(20, len(df)):
        window = df.iloc[i-10:i+1]
        signals = 0
        notes = []

        if df['SMA10'].iloc[i] > df['SMA50'].iloc[i]:
            signals += 1
            notes.append("SMA10>SMA50")
        if df['SMA50'].iloc[i] > df['SMA200'].iloc[i]:
            signals += 1
            notes.append("SMA50>SMA200")
        if zone and zone.get('low') <= df['Close'].iloc[i] <= zone.get('high'):
            signals += 1
            notes.append("In balance zone")
        if bb_threshold is not None and bb_width.iloc[i] <= bb_threshold:
            signals += 1
            notes.append("Squeeze")
        if tech._detect_2b(window):
            signals += 1
            notes.append("2B pattern")
        seq = sequence.analyze(df['Close'].iloc[i])
        if seq.get('is_holy_trinity') or seq.get('is_palindrome'):
            signals += 1
            notes.append("Sequence level")

        if signals >= threshold:
            event = {
                "Date": df.index[i].date(),
                "Timeframe": TIMEFRAME_OPTIONS.get(tf, {}).get("label", tf),
                "Signal": "High confluence",
                "Context": "; ".join(notes) if notes else "Multi-signal alignment"
            }
            apply_event_outcome(event, df, i)
            events.append(event)

    return events

def apply_event_outcome(event, df, idx):
    event_price = df['Close'].iloc[idx]
    future = df.iloc[idx:]
    if future.empty:
        event["Delta %"] = 0
        event["Peak %"] = 0
        event["Trough %"] = 0
        return
    delta = (future['Close'].iloc[-1] - event_price) / event_price * 100
    peak = (future['High'].max() - event_price) / event_price * 100
    trough = (future['Low'].min() - event_price) / event_price * 100
    event["Delta %"] = round(delta, 2)
    event["Peak %"] = round(peak, 2)
    event["Trough %"] = round(trough, 2)

def build_signal_markers(data, tf):
    markers = []
    events = build_timeline_for_df(data, tf)
    if not events:
        return markers
    for event in events[:12]:
        event_date = pd.to_datetime(event["Date"])
        nearest = data.loc[data.index <= event_date].tail(1)
        if nearest.empty:
            continue
        price = float(nearest['Close'].iloc[0])
        hover = f"{event['Signal']} | {event['Timeframe']}<br>{event['Context']}<br>Delta {event['Delta %']}%"
        markers.append({"date": event_date, "price": price, "hover": hover})
    return markers

def select_balance_zone_near_price(data, current_price, lookback_days=756):
    """Pick the most relevant balance zone near the current price."""
    if data is None or data.empty or current_price is None:
        return None
    recent = data.tail(lookback_days)
    if recent.empty:
        return None

    tech = TechnicalAnalyzer()
    balance = tech._analyze_balance_zones(recent)
    zones = balance.get("zones", [])
    if not zones:
        return None

    for zone in zones:
        if zone.get("low") <= current_price <= zone.get("high"):
            return zone

    def zone_distance(z):
        low = z.get("low")
        high = z.get("high")
        if low is None or high is None:
            return float("inf")
        return min(abs(current_price - low), abs(current_price - high))

    nearest = min(zones, key=zone_distance)
    if zone_distance(nearest) > current_price * 0.35:
        return None
    return nearest

def build_event_markers(data):
    """Limit historical events to the visible data window."""
    if data is None or data.empty:
        return []
    start = data.index.min()
    end = data.index.max()
    markers = []
    for item in HISTORICAL_EVENTS:
        event_date = pd.to_datetime(item["date"])
        if start <= event_date <= end:
            markers.append({"date": event_date, "label": item["label"]})
    return markers

def build_behavioral_context():
    """Return timing heuristics in plain language."""
    try:
        now = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now = datetime.now()
    day = now.strftime("%A")
    day_map = {
        "Monday": "Monday is context day. Gaps often fade and the market feels out the week.",
        "Tuesday": "Tuesday is a momentum day. Breakouts and trend follow-through are more reliable.",
        "Wednesday": "Wednesday leans toward balance. Fading extremes often works when structure is clean.",
        "Thursday": "Thursday tends to flip. Reversal risk rises and narratives matter more.",
        "Friday": "Friday is shape day. Breakouts tend to stall unless the move is already mature."
    }

    time_notes = []
    current_time = now.time()
    key_windows = [
        ((9, 30), (10, 30), "Open window. First-hour range sets the tone."),
        ((11, 15), (11, 45), "Europe close zone. Often a liquidity pivot."),
        ((14, 15), (14, 45), "2:30pm handoff. Momentum can shift."),
        ((15, 30), (16, 0), "Power hour. Late-day acceleration or fade."),
        ((20, 0), (20, 30), "Asia open. Liquidity can reprice quickly."),
        ((0, 0), (0, 20), "Midnight roll. New day resets positioning."),
        ((3, 0), (3, 30), "Europe open. Direction can reprice."),
        ((5, 15), (5, 45), "Early Europe pulse. Direction can flip."),
        ((7, 15), (7, 45), "Pre-market build. Watch for fake moves.")
    ]
    for (start_h, start_m), (end_h, end_m), note in key_windows:
        start_time = datetime.strptime(f"{start_h}:{start_m}", "%H:%M").time()
        end_time = datetime.strptime(f"{end_h}:{end_m}", "%H:%M").time()
        if start_time <= current_time <= end_time:
            time_notes.append(note)

    if not time_notes:
        time_notes.append("No key timing window right now. Let structure lead.")

    day_note = day_map.get(day, "Timing context unavailable today.")
    month_note = ""
    if now.day in [1, 2]:
        month_note = "Month start tends to bring fresh flows."
    elif now.day in [14, 15]:
        month_note = "Mid-month can flip the trend if structure weakens."
    elif now.day == 21:
        month_note = "Volatility day. Expect larger swings."
    elif now.day == 24:
        month_note = "The 24th often carries surprise risk. Keep stops honest."
    elif now.day >= 28:
        month_note = "Month-end flows can skew direction."

    notes = [day_note] + time_notes
    if month_note:
        notes.append(month_note)
    notes.append("Treat headlines as retail fuel. Let structure confirm the story.")
    return notes

def build_if_then_scenarios(result):
    """Generate if/then scenarios for near-term setup evolution."""
    scenarios = []
    data = result.get("data", {}).get("daily")
    zone = select_balance_zone_near_price(data, result.get("current_price"), lookback_days=756)
    technical = result.get('layers', {}).get('technical', {})

    if zone:
        high = zone.get('high')
        low = zone.get('low')
        if high and low:
            scenarios.append(f"If price holds above {high:.2f}, bias favors breakout continuation.")
            scenarios.append(f"If price slips below {low:.2f}, failure implies mean reversion into the next balance zone.")

    touch_rank = None
    if data is not None and not data.empty:
        tech = TechnicalAnalyzer()
        balance = tech._analyze_balance_zones(data.tail(756))
        touch_rank = balance.get('touch_rank')
    if touch_rank:
        scenarios.append(f"{touch_rank} at the balance zone. Later touches often lead to a break, not a hold.")

    ma_signal = result.get('layers', {}).get('ma_system', {}).get('signal', 'None')
    if ma_signal == 'Long':
        scenarios.append("If SMA10 stays above SMA50, trend continuation stays valid.")
    elif ma_signal == 'Short':
        scenarios.append("If SMA10 stays below SMA50, downside momentum can stay in play.")
    else:
        scenarios.append("If SMA10/SMA50 cross, the trend regime will get clearer.")

    if technical.get('bollinger_squeeze'):
        scenarios.append("If volatility expands from this squeeze, historically resolves as a fast directional move.")

    return scenarios

@st.cache_data(ttl=3600, show_spinner=False)
def cached_ticker_profile(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.get_info()
    except Exception:
        info = {}
    return info or {}

@st.cache_data(ttl=3600, show_spinner=False)
def cached_ticker_calendar(ticker):
    try:
        stock = yf.Ticker(ticker)
        cal = stock.calendar
        if isinstance(cal, pd.DataFrame) and not cal.empty:
            return cal
    except Exception:
        return None
    return None

def build_company_summary(ticker):
    info = cached_ticker_profile(ticker)
    quote_type = info.get("quoteType")
    name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector")
    industry = info.get("industry")
    if quote_type == "ETF":
        return f"{name} is an ETF tracking a major index or sector basket."
    if sector and industry:
        return f"{name} is a {industry} name in the {sector} sector."
    if sector:
        return f"{name} operates in the {sector} sector."
    return f"{name} overview is not fully available."

def build_upcoming_events(ticker):
    calendar = cached_ticker_calendar(ticker)
    if calendar is None or calendar.empty:
        return []
    events = []
    for idx, row in calendar.iterrows():
        date_val = row[0] if len(row) else None
        if pd.isna(date_val):
            continue
        events.append(f"{idx}: {pd.to_datetime(date_val).date()}")
    return events

def build_timeframe_overview(result):
    rows = []
    for tf, data in result.get("layers", {}).get("timeframes", {}).items():
        if data.get("error"):
            continue
        regime = data.get("ma_regime", "Unknown")
        tech = data.get("technical", {})
        balance_state = tech.get("balance_state") if isinstance(tech, dict) else None
        state = classify_market_state(regime, balance_state)
        positives = []
        negatives = []
        if state == "Bullish":
            positives.append("Trend up")
        elif state == "Bearish":
            negatives.append("Trend down")
        if balance_state == "in_balance":
            negatives.append("Choppy balance")
        if tech.get("bollinger_squeeze"):
            positives.append("Squeeze setup")
        if tech.get("structure_flags"):
            negatives.append("Imbalance")

        rows.append({
            "Timeframe": TIMEFRAME_OPTIONS.get(tf, {}).get("label", tf),
            "State": state,
            "Positives": ", ".join(positives) if positives else "—",
            "Negatives": ", ".join(negatives) if negatives else "—"
        })
    return rows

def build_bull_bear_cases(result):
    data = result.get("data", {}).get("daily")
    zone = select_balance_zone_near_price(data, result.get("current_price"), lookback_days=756)
    sequence = result.get("layers", {}).get("sequence", {})
    magnets = sequence.get("next_magnets", []) if sequence else []

    if zone:
        support = zone.get("low")
        resistance = zone.get("high")
        midpoint = (support + resistance) / 2 if support and resistance else None
    else:
        support = float(data['Low'].tail(60).min()) if data is not None and not data.empty else None
        resistance = float(data['High'].tail(60).max()) if data is not None and not data.empty else None
        midpoint = (support + resistance) / 2 if support and resistance else None

    bull_targets = [m for m in magnets if support is None or m > support][:3]
    bear_targets = [m for m in magnets if resistance is None or m < resistance][:3]

    score = result.get("confluence_score", 0)
    confidence = "High" if score >= 9 else "Medium" if score >= 6 else "Low"

    return {
        "support": support,
        "resistance": resistance,
        "midpoint": midpoint,
        "bull_targets": bull_targets,
        "bear_targets": bear_targets,
        "confidence": confidence
    }

def build_overview_sentence(result):
    ticker = result.get("ticker", "")
    state = result.get("market_state", "Choppy")
    risk = result.get("risk_level", "Unknown")
    data = result.get("data", {}).get("daily")
    zone = select_balance_zone_near_price(data, result.get("current_price"), lookback_days=756)
    if zone:
        zone_text = f"Balance zone {zone.get('low', 0):.2f} to {zone.get('high', 0):.2f}."
    else:
        zone_text = "Balance zone still forming."
    return (
        f"{ticker} reads {state} with {risk} risk. {zone_text} "
        "Confluence is context for swings, not a trigger. It blends trend, balance, sequence levels, and volatility."
    )
def build_historian_summary(data):
    """Attach price context to major historical events."""
    if data is None or data.empty:
        return []

    summary = []

    for event in HISTORICAL_EVENTS:
        date = pd.to_datetime(event["date"])
        nearest = data.loc[data.index <= date].tail(1)
        if nearest.empty:
            continue
        price = float(nearest['Close'].iloc[0])
        window = data.loc[(data.index >= date - timedelta(days=20)) & (data.index <= date + timedelta(days=20))]
        if window.empty:
            window = data.loc[data.index <= date].tail(40)
        peak = float(window['High'].max()) if not window.empty else price
        trough = float(window['Low'].min()) if not window.empty else price
        if price <= trough * 1.02:
            note = "Event marked a breakdown level."
        elif price >= peak * 0.98:
            note = "Event marked a reversal level."
        else:
            note = "Event marked a key reference level."
        summary.append({
            "date": date.date(),
            "event": event["label"],
            "price": price,
            "note": note
        })
    return summary

def build_combined_macro(snapshot):
    """Combine macro snapshots into a composite badge."""
    scores = []
    risk_points = []
    short_states = []
    mid_states = []
    long_states = []
    for symbol in MACRO_SYMBOLS:
        item = snapshot.get(symbol)
        if not item:
            continue
        scores.append(item.get('confluence_score', 0))
        risk_level = item.get('risk_level', 'Moderate')
        risk_points.append({'Low': 0, 'Moderate': 1, 'High': 2}.get(risk_level, 1))
        states = item.get("market_states", {})
        short_states.append(states.get("short"))
        mid_states.append(states.get("mid"))
        long_states.append(states.get("long"))

    if not scores:
        return {'confluence_score': 0, 'risk_level': 'Unknown', 'headline_signal': 'Macro snapshot unavailable.'}

    combined_score = int(round(sum(scores) / len(scores)))
    avg_risk = sum(risk_points) / len(risk_points) if risk_points else 1
    risk_level = 'Low' if avg_risk < 0.7 else 'Moderate' if avg_risk < 1.5 else 'High'
    headline = "Macro alignment is steady." if combined_score >= 7 else "Macro alignment is mixed."
    horizon_states = {
        "short": combine_states(short_states),
        "mid": combine_states(mid_states),
        "long": combine_states(long_states)
    }
    combined_state = combine_states(list(horizon_states.values()))

    return {
        'confluence_score': combined_score,
        'risk_level': risk_level,
        'headline_signal': headline,
        'market_state': combined_state,
        'market_states': horizon_states
    }

def render_macro_header(snapshot):
    """Render the macro badge header."""
    cards = []
    for symbol in MACRO_SYMBOLS:
        item = snapshot.get(symbol, {})
        score = item.get('confluence_score', 0)
        risk = item.get('risk_level', 'Unknown')
        state = item.get('market_state', 'Choppy')
        states = item.get('market_states', {})
        href = f"?symbol={symbol}&view=symbol"
        pill_class = "pill-green" if risk == "Low" else "pill-accent" if risk == "High" else "pill"
        state_class = "state-bull" if state == "Bullish" else "state-bear" if state == "Bearish" else "state-chop"
        cards.append(
            f"<a class='macro-card' href='{href}'>"
            f"<div class='macro-title'>{symbol}</div>"
            f"<div class='macro-metric'>Confluence {score}/12</div>"
            f"<div class='subtle'>Risk: {risk}</div>"
            f"<div class='state-label'><span class='state-dot {state_class}'></span>{state}</div>"
            f"<div class='subtle'>S:{states.get('short','-')} | M:{states.get('mid','-')} | L:{states.get('long','-')}</div>"
            f"<span class='pill {pill_class}'>Point-in-time</span>"
            f"</a>"
        )

    combined = snapshot.get("COMBINED", {})
    combined_score = combined.get('confluence_score', 0)
    combined_risk = combined.get('risk_level', 'Unknown')
    combined_state = combined.get('market_state', 'Choppy')
    combined_states = combined.get('market_states', {})
    combined_class = "pill-green" if combined_risk == "Low" else "pill-accent" if combined_risk == "High" else "pill"
    combined_state_class = "state-bull" if combined_state == "Bullish" else "state-bear" if combined_state == "Bearish" else "state-chop"
    cards.append(
        f"<a class='macro-card' href='?view=macro'>"
        f"<div class='macro-title'>MACRO</div>"
        f"<div class='macro-metric'>Composite {combined_score}/12</div>"
        f"<div class='subtle'>Risk: {combined_risk}</div>"
        f"<div class='state-label'><span class='state-dot {combined_state_class}'></span>{combined_state}</div>"
        f"<div class='subtle'>S:{combined_states.get('short','-')} | M:{combined_states.get('mid','-')} | L:{combined_states.get('long','-')}</div>"
        f"<span class='pill {combined_class}'>Combined signal</span>"
        f"</a>"
    )

    # Add Philosophy card
    cards.append(
        f"<a class='macro-card' href='?view=philosophy'>"
        f"<div class='macro-title'>PHILOSOPHY</div>"
        f"<div class='macro-metric'>What is COREXIA?</div>"
        f"<div class='subtle'>Category definition</div>"
        f"<div class='state-label'>Market Intelligence</div>"
        f"<div class='subtle'>Sensemaking, not signaling</div>"
        f"<span class='pill'>Read</span>"
        f"</a>"
    )

    st.markdown("<div class='macro-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)
    st.caption("Click a badge to open its full analysis page.")

def render_philosophy_page():
    """Display COREXIA philosophy and category definition."""

    st.markdown("# WHAT IS COREXIA?")

    st.markdown("## Category")
    st.write("**Market Intelligence Workstation**")

    st.markdown("## One-Sentence Definition")
    st.write(
        "COREXIA is a market intelligence workstation that fuses structure, regime, "
        "volatility, and historical market memory into a coherent real-time market narrative."
    )

    st.markdown("## What COREXIA Is")
    st.write("✓ A sensemaking engine")
    st.write("✓ A context compressor")
    st.write("✓ A memory-aware market map")

    st.markdown("## What COREXIA Is NOT")
    st.write("✗ Not a signal service")
    st.write("✗ Not a trading strategy")
    st.write("✗ Not an execution platform")
    st.write("✗ Not predictive analytics")

    st.markdown("## Comparable Mental Models")
    st.write("• Sell-side desk market monitors")
    st.write("• Internal macro dashboards")
    st.write("• PM briefing terminals")

    st.divider()

    st.markdown("## The Core Principle")
    st.info(
        "**COREXIA does not tell you what to trade. "
        "It tells you what kind of market you are standing in.**"
    )

    st.markdown("## Philosophy")
    st.write(
        "Markets are not predicted — they are understood. COREXIA compresses "
        "institutional-grade confluence, market memory, and regime analysis into "
        "a single coherent narrative that answers: *What kind of market am I in right now?*"
    )

    st.write(
        "Confluence is context, not a trade trigger. It blends trend, balance, "
        "sequence levels, and volatility into a readable state machine. "
        "The system does not optimize entries or exits. It provides the structural "
        "awareness necessary for discretionary decision-making."
    )

    st.write(
        "COREXIA is built for operators who think in regimes, not signals."
    )

    st.divider()

    st.markdown("## Architecture")
    st.write("**Analysis Layers:**")
    st.write("• Market Memory (breadth, ratios, volatility)")
    st.write("• Regime Detection (macro, Fed policy, Wyckoff)")
    st.write("• Sequence Map (price magnets, behavioral floors)")
    st.write("• MA System (10/50/200 trend compass)")
    st.write("• Technical Confluence (patterns, structure, volume)")
    st.write("• Balance Structure (value zones, touch fatigue)")

    st.write("\n**Synthesis Outputs:**")
    st.write("• Market Narrative Spine (forced 1-2 sentence synthesis)")
    st.write("• Confluence Attribution (causal explanation)")
    st.write("• Market Friction (difficulty expressing edge)")
    st.write("• Cross-Asset Narrative (coherence check)")
    st.write("• Market Memory Trace (behavioral records)")


def render_macro_overview(snapshot, settings):
    combined = snapshot.get("COMBINED", {})
    now = datetime.now()

    st.markdown("**COREXIA MARKET STATION**")
    if st.button("↻ Refresh Station"):
        st.session_state.cache_bust += 1
        st.rerun()
    st.write(f"Welcome. Today is {now.strftime('%A, %B %d, %Y')}.")
    st.write(combined.get("headline_signal", "Macro snapshot unavailable."))

    st.markdown("**Macro Stage**")
    st.write(f"State: {combined.get('market_state', 'Choppy')} | Risk: {combined.get('risk_level', 'Unknown')}")
    st.write("Macro blend uses weekly, daily, 4H, and 90M structure. Time is a confluence input.")

    rows = []
    for symbol in MACRO_SYMBOLS:
        item = snapshot.get(symbol, {})
        states = item.get("market_states", {})
        rows.append({
            "Symbol": symbol,
            "Confluence": item.get("confluence_score", 0),
            "State": item.get("market_state", "Choppy"),
            "S/M/L": f"{states.get('short','-')}/{states.get('mid','-')}/{states.get('long','-')}",
            "Friction": item.get("market_friction", "Unknown")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Cross-Asset Narrative
    st.divider()
    st.markdown("**CROSS-ASSET NARRATIVE**")
    narrative, confidence = build_cross_asset_narrative(snapshot)
    st.write(narrative)
    st.caption(f"Narrative confidence: {confidence}")
    st.divider()

    st.markdown("**Macro Releases (latest)**")
    api_key = resolve_alpha_key()
    if api_key:
        macro_events = cached_macro_events(api_key)
        if macro_events:
            for item in macro_events[:6]:
                date = item.get("timestamp").date() if item.get("timestamp") else "N/A"
                value = item.get("value", "N/A")
                st.write(f"- {item.get('title')} | {date} | {value}")
        else:
            st.write("No macro releases returned.")
    else:
        st.write("Alpha Vantage key missing. Macro releases not loaded.")

    st.markdown("**Macro News (headline flow)**")
    if api_key:
        market_news = cached_market_news(api_key)
        if market_news:
            for item in market_news[:6]:
                title = item.get("title", "Untitled")
                source = item.get("source", "Source")
                st.write(f"- {title} ({source})")
        else:
            st.write("No market news returned.")
    else:
        st.write("Alpha Vantage key missing. News sentiment not loaded.")

def render_symbol_analysis(result, settings):
    ticker = result.get("ticker", "")
    st.markdown(f"**{ticker} — Point-in-Time Analysis**")

    summary = build_company_summary(ticker)
    events = build_upcoming_events(ticker)

    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.write(summary)
        if events:
            st.write("Upcoming events: " + "; ".join(events[:2]))
        else:
            st.write("Upcoming events: No earnings date detected.")
    with header_col2:
        st.metric("Confluence", f"{result.get('confluence_score', 0)}/12")

        # Display new market state with color coding
        market_state = result.get('market_state', 'RANGE')
        direction_bias = result.get('direction_bias', 'Neutral')

        # Color coding for states
        state_colors = {
            "TRENDING": "#3b82f6",      # blue
            "TRANSITION": "#f59e0b",    # amber
            "RANGE": "#6b7280",         # neutral gray
            "STRESSED": "#ef4444"       # red
        }
        state_color = state_colors.get(market_state, "#6b7280")

        st.markdown(f"**Market State:** <span style='color:{state_color};font-weight:bold;'>{market_state}</span>", unsafe_allow_html=True)
        st.metric("Bias", direction_bias)
        st.metric("Friction", result.get("market_friction", "Unknown"))
        st.metric("Last Price", f"${result['current_price']:.2f}")
        st.caption(result['scan_time'].strftime("%Y-%m-%d %H:%M"))

    # Market Narrative Spine
    st.divider()
    st.markdown("### MARKET SPINE")
    spine = build_market_spine(result)
    st.write(spine)
    st.write("**Context:** " + build_headline_context(result))
    st.caption("This is what the market is, not what it might do.")

    # Confluence Attribution
    st.markdown("**CONFLUENCE ATTRIBUTION**")
    drivers, gaps = build_confluence_attribution(result['checklist'])

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Drivers:**")
        for driver in drivers:
            st.write(f"✓ {driver}")

    with col2:
        st.write("**Gaps:**")
        for gap in gaps:
            st.write(f"○ {gap}")

    st.caption("This explains why the confluence number is what it is.")
    st.divider()

    st.markdown("**Analysis Overview**")
    st.write(build_overview_sentence(result))
    st.markdown("**If/Then Outlook**")
    for line in build_if_then_scenarios(result):
        st.write(f"- {line}")

    overview_rows = build_timeframe_overview(result)
    if overview_rows:
        st.dataframe(pd.DataFrame(overview_rows), use_container_width=True, hide_index=True)

    cases = build_bull_bear_cases(result)
    case_cols = st.columns(2)
    with case_cols[0]:
        st.markdown("**Bull Case (Swing)**")
        if cases["support"] is not None and cases["resistance"] is not None:
            st.write(f"Support: {cases['support']:.2f}")
            st.write(f"Midpoint: {cases['midpoint']:.2f}" if cases["midpoint"] else "Midpoint: N/A")
            st.write(f"Resistance: {cases['resistance']:.2f}")
        if cases["bull_targets"]:
            st.write("Targets: " + ", ".join([f"{t:.2f}" for t in cases["bull_targets"]]))
        st.caption(f"Confidence: {cases['confidence']}")

    with case_cols[1]:
        st.markdown("**Bear Case (Swing)**")
        if cases["support"] is not None and cases["resistance"] is not None:
            st.write(f"Resistance: {cases['resistance']:.2f}")
            st.write(f"Midpoint: {cases['midpoint']:.2f}" if cases["midpoint"] else "Midpoint: N/A")
            st.write(f"Support: {cases['support']:.2f}")
        if cases["bear_targets"]:
            st.write("Targets: " + ", ".join([f"{t:.2f}" for t in cases["bear_targets"]]))
        st.caption(f"Confidence: {cases['confidence']}")

    st.divider()
    chart_cols = st.columns([3, 1])
    with chart_cols[0]:
        chart_tf = st.radio("Chart Timeframe", ["1W", "1D", "4H", "90M"], horizontal=True, index=1)
    with chart_cols[1]:
        chart_range = st.radio("Chart Range", ["6M", "1Y", "5Y", "YTD", "20Y"], horizontal=True, index=1)
    display_price_chart(result, chart_tf, chart_range)

    st.divider()
    display_signal_timeline(result)

    with st.expander("Deep Dive Layers", expanded=False):
        display_market_memory(result)
        display_sequence_analysis(result)
        display_balance_structure(result)
        display_ma_system(result)
        display_technical_analysis(result)
        display_timeframe_alignment(result, "1D")
        display_event_feed(result)

def render_confluence_scanner(settings):
    st.markdown("**Top Confluence Names (Swing Focus)**")
    st.caption("Auto-scanned across each index universe. Bullish and bearish lists are mid-term aligned.")

    index_cols = st.columns(2)
    with index_cols[0]:
        for index_name in ["SPY", "QQQ"]:
            results = cached_top_confluence(index_name, settings["cache_bust"])
            st.markdown(f"**{index_name} — Bullish**")
            st.dataframe(pd.DataFrame(results["bullish"]), use_container_width=True, hide_index=True)
            st.markdown(f"**{index_name} — Bearish**")
            st.dataframe(pd.DataFrame(results["bearish"]), use_container_width=True, hide_index=True)
            st.caption(f"Scanned {results['scanned']} of {results['total']} symbols.")

    with index_cols[1]:
        for index_name in ["IWM", "DIA"]:
            results = cached_top_confluence(index_name, settings["cache_bust"])
            st.markdown(f"**{index_name} — Bullish**")
            st.dataframe(pd.DataFrame(results["bullish"]), use_container_width=True, hide_index=True)
            st.markdown(f"**{index_name} — Bearish**")
            st.dataframe(pd.DataFrame(results["bearish"]), use_container_width=True, hide_index=True)
            st.caption(f"Scanned {results['scanned']} of {results['total']} symbols.")

def calculate_checklist(layers):
    """
    The sacred 12-point checklist - higher scores mean stronger alignment
    """
    checklist = {
        'trendline_zone': False,
        '2b_or_pattern': False,
        'imbalance': False,
        'volume_anomaly': False,
        'proxy_memory': False,
        'intermarket_divergence': False,
        'sequence_level': False,
        'curvature': False,
        'balance_zone': False,
        'liquidity_grab': False,
        'htf_structure': False,
        'space_vacuum': False
    }
    
    # Check each point based on layer results
    
    # 1. Trendline Zone
    if 'technical' in layers and layers['technical']:
        checklist['trendline_zone'] = layers['technical'].get('trendline_hit', False)
    
    # 2. 2B or Pattern
    if 'technical' in layers and layers['technical']:
        patterns = layers['technical'].get('patterns', {})
        checklist['2b_or_pattern'] = any([
            patterns.get('2b', False),
            patterns.get('diving_duck', False),
            patterns.get('pop', False)
        ])
    
    # 3. Imbalance
    if 'technical' in layers and layers['technical']:
        checklist['imbalance'] = layers['technical'].get('unfilled_gaps', False)
    
    # 4. Volume Anomaly
    if 'technical' in layers and layers['technical']:
        checklist['volume_anomaly'] = layers['technical'].get('volume_climax', False)
    
    # 5. Proxy Memory
    if 'market_memory' in layers and layers['market_memory']:
        checklist['proxy_memory'] = layers['market_memory'].get('zone_hit', False)
    
    # 6. Intermarket Divergence
    if 'market_memory' in layers and layers['market_memory']:
        checklist['intermarket_divergence'] = layers['market_memory'].get('divergence', False)
    
    # 7. Sequence Level (Holy Trinity or Palindrome)
    if 'sequence' in layers and layers['sequence']:
        checklist['sequence_level'] = (
            layers['sequence'].get('is_holy_trinity', False) or
            layers['sequence'].get('is_palindrome', False)
        )
    
    # 8. Curvature
    if 'technical' in layers and layers['technical']:
        checklist['curvature'] = layers['technical'].get('curvature', False)
    
    # 9. Balance Zone / Value Area
    if 'technical' in layers and layers['technical']:
        checklist['balance_zone'] = layers['technical'].get('balance_zone', False)
    
    # 10. Liquidity Grab
    if 'technical' in layers and layers['technical']:
        checklist['liquidity_grab'] = layers['technical'].get('stophunt_complete', False)
    
    # 11. HTF Structure
    if 'timeframes' in layers and layers['timeframes']:
        htf_aligned = False
        for tf, tf_data in layers['timeframes'].items():
            if tf in ['1W', '1D'] and tf_data.get('ma_regime') not in ['Neutral', None]:
                htf_aligned = True
        checklist['htf_structure'] = htf_aligned
    
    # 12. Space Vacuum (imbalance or squeeze)
    if 'technical' in layers and layers['technical']:
        checklist['space_vacuum'] = layers['technical'].get('vacuum', False) or layers['technical'].get('bollinger_squeeze', False)
    
    return checklist

WEIGHTED_CHECKLIST = {
    'trendline_zone': 1.0,
    '2b_or_pattern': 1.5,
    'imbalance': 1.0,
    'volume_anomaly': 1.0,
    'proxy_memory': 1.0,
    'intermarket_divergence': 0.5,
    'sequence_level': 1.0,
    'curvature': 0.5,
    'balance_zone': 1.0,
    'liquidity_grab': 1.0,
    'htf_structure': 1.0,
    'space_vacuum': 1.0
}

def calculate_weighted_score(checklist):
    """Calculate weighted confluence score."""
    max_score = sum(WEIGHTED_CHECKLIST.values())
    score = 0
    for key, weight in WEIGHTED_CHECKLIST.items():
        if checklist.get(key):
            score += weight
    normalized = int(round((score / max_score) * 12)) if max_score else 0
    return round(score, 2), round(max_score, 2), normalized


def build_confluence_attribution(checklist):
    """
    Explain WHY the confluence score is what it is.

    Returns: (drivers, gaps)
    - drivers: Top 3 checklist items that ARE present
    - gaps: Top 3 checklist items that are MISSING

    System chooses based on weight contribution.
    """
    # Build weighted presence/absence lists
    present = []
    absent = []

    for key, is_present in checklist.items():
        weight = WEIGHTED_CHECKLIST.get(key, 1.0)
        label = key.replace('_', ' ').title()

        if is_present:
            present.append((label, weight))
        else:
            absent.append((label, weight))

    # Sort by weight descending
    present.sort(key=lambda x: x[1], reverse=True)
    absent.sort(key=lambda x: x[1], reverse=True)

    # Take top 3 of each
    drivers = [label for label, _ in present[:3]]
    gaps = [label for label, _ in absent[:3]]

    return drivers, gaps

def determine_primary_state(result):
    """
    Classify market into one of four mutually exclusive states.

    This replaces the old Bullish/Bearish/Choppy taxonomy with
    a more informative regime classification.

    Returns: ("TRENDING" | "TRANSITION" | "RANGE" | "STRESSED", direction_bias)
    """
    # Inputs
    horizons = result.get("market_states", {})
    ma_system = result.get("layers", {}).get("ma_system", {})
    technical = result.get("layers", {}).get("technical", {})

    ma_regime = ma_system.get("regime", "Neutral")
    signal = ma_system.get("signal", "None")
    balance_state = technical.get("structure", {}).get("balance_state")
    squeeze = technical.get("bollinger_squeeze", False)

    # Get touch rank for fatigue
    data = result.get("data", {}).get("daily")
    touch_rank = None
    if data is not None and not data.empty:
        tech_analyzer = TechnicalAnalyzer()
        balance = tech_analyzer._analyze_balance_zones(data.tail(756))
        touch_rank = balance.get('touch_rank')

    # State 1: STRESSED (highest priority - structural tension)
    fatigue = touch_rank and "Fourth" in touch_rank
    high_vol = technical.get("volume", {}).get("climax_detected", False)

    if fatigue or (high_vol and balance_state in ["breakout_up", "breakdown_down"]):
        direction = "Bullish" if balance_state == "breakout_up" else "Bearish" if balance_state == "breakdown_down" else "Neutral"
        return "STRESSED", direction

    # State 2: TRENDING (strong directional control)
    htf_aligned = (
        horizons.get("long") == horizons.get("mid") and
        horizons.get("long") in ["Bullish", "Bearish"]
    )
    price_extended = balance_state in ["breakout_up", "breakdown_down"]

    if htf_aligned and ma_regime in ["Bull", "Bear"] and price_extended:
        direction = "Bullish" if ma_regime == "Bull" else "Bearish"
        return "TRENDING", direction

    # State 3: TRANSITION (regime shift in progress)
    ma_crossover_active = signal in ["Long", "Short", "Exit Long", "Exit Short"]
    htf_conflict = horizons.get("long") != horizons.get("mid")

    if ma_crossover_active or (htf_conflict and price_extended):
        # Directional bias = where momentum is pointing
        if signal in ["Long", "Short"]:
            direction = "Bullish" if signal == "Long" else "Bearish"
        elif ma_regime in ["Bull", "Bear"]:
            direction = "Bullish" if ma_regime == "Bull" else "Bearish"
        else:
            direction = "Neutral"
        return "TRANSITION", direction

    # State 4: RANGE (default for balance + low volatility)
    if balance_state == "in_balance" or (ma_regime == "Neutral" and not price_extended):
        return "RANGE", "Neutral"

    # Fallback (shouldn't reach here often)
    return "RANGE", "Neutral"


def classify_market_state(ma_regime, balance_state):
    """
    DEPRECATED: Legacy function for backward compatibility.
    Use determine_primary_state() instead for new code.
    """
    # Old logic preserved for modules that still call this
    if balance_state == "in_balance":
        return "Choppy"
    if ma_regime == "Bull":
        return "Bullish"
    if ma_regime == "Bear":
        return "Bearish"
    return "Choppy"

def combine_states(states):
    """Blend multiple states into one."""
    states = [s for s in states if s]
    if not states:
        return "Choppy"
    if all(s == "Bullish" for s in states):
        return "Bullish"
    if all(s == "Bearish" for s in states):
        return "Bearish"
    if "Choppy" in states:
        return "Choppy"
    return "Choppy"

def compute_state_by_horizon(layers):
    """Compute short/mid/long state from timeframe signals."""
    timeframes = layers.get("timeframes", {})
    def tf_state(tf):
        data = timeframes.get(tf, {})
        if not data or data.get("error"):
            return None
        ma_regime = data.get("ma_regime")
        balance_state = None
        tech = data.get("technical", {})
        if isinstance(tech, dict):
            balance_state = tech.get("balance_state")
        return classify_market_state(ma_regime, balance_state)

    short_states = [tf_state("90M"), tf_state("4H")]
    mid_state = tf_state("1D")
    long_state = tf_state("1W")

    return {
        "short": combine_states(short_states),
        "mid": mid_state or "Choppy",
        "long": long_state or "Choppy"
    }

def assess_market_friction(result):
    """
    Assess market friction based on structural clarity, volatility, and regime alignment.

    Friction measures difficulty expressing an edge, not capital risk.
    - Low friction = structure is clean, directional control is clear
    - High friction = chop, overlap, unresolved balance

    Returns: (friction_level, friction_signal)
    """
    friction_points = 0

    regime = result.get('layers', {}).get('regime', {}).get('macro', 'Unknown')
    ma_regime = result.get('layers', {}).get('ma_system', {}).get('regime', 'Unknown')
    technical = result.get('layers', {}).get('technical', {})
    balance_state = technical.get('structure', {}).get('balance_state')

    # Regime clarity (2 pts possible)
    if regime in ['Unknown', 'Transitional']:
        friction_points += 1
    if ma_regime in ['Neutral', 'Unknown']:
        friction_points += 1

    # Balance overlap (3 pts possible - elevated weight)
    if balance_state == 'in_balance':
        friction_points += 2  # Strong friction signal
    if technical.get('balance_zone') and balance_state in ['breakdown_down', 'breakout_up']:
        friction_points += 1  # Structural tension

    # Structural imbalance (1 pt)
    if technical.get('unfilled_gaps'):
        friction_points += 1

    # Volatility state (1 pt)
    market_memory = result.get('layers', {}).get('market_memory', {})
    vix_data = market_memory.get('volatility', {}).get('vix', {})
    if vix_data and vix_data.get('extreme'):
        friction_points += 1

    # Confluence sparsity (1 pt)
    if result.get('confluence_score', 0) <= 4:
        friction_points += 1

    # Map points to friction level
    if friction_points <= 2:
        level = "Low"
        signal = "Structure is clean. Directional control is clear."
    elif friction_points <= 4:
        level = "Moderate"
        signal = "Structure is mixed. Demand confirmation and tighter structure."
    else:
        level = "High"
        signal = "Overlapping structure. Expect chop and protect capital."

    return level, signal


def assess_risk_level(result):
    """Legacy wrapper for assess_market_friction(). Use assess_market_friction() for new code."""
    return assess_market_friction(result)


def build_market_spine(result):
    """
    Generate authoritative 1-2 sentence market narrative.

    This is forced synthesis, not commentary.
    - Max 2 sentences
    - Declarative, present-state
    - No numbers, no if/then, no advice

    Output: "What kind of market am I standing in?"
    """
    state = result.get("market_state")
    horizons = result.get("market_states", {})
    friction = result.get("market_friction")
    technical = result.get("layers", {}).get("technical", {})
    balance_state = technical.get("structure", {}).get("balance_state")
    squeeze = technical.get("bollinger_squeeze")

    # Get touch rank for structure fatigue
    data = result.get("data", {}).get("daily")
    touch_rank = None
    if data is not None and not data.empty:
        tech_analyzer = TechnicalAnalyzer()
        balance = tech_analyzer._analyze_balance_zones(data.tail(756))
        touch_rank = balance.get('touch_rank')

    sentences = []

    # Sentence 1: Structural state (higher timeframe)
    long_state = horizons.get("long")
    mid_state = horizons.get("mid")

    if long_state == "Bullish" and mid_state == "Bullish":
        sentences.append(
            "Higher-timeframe structure remains bullish, anchoring the broader market context."
        )
    elif long_state == "Bearish" and mid_state == "Bearish":
        sentences.append(
            "Higher-timeframe structure is bearish, defining a defensive market backdrop."
        )
    elif long_state == "Bullish" and mid_state != "Bullish":
        sentences.append(
            "Higher-timeframe structure is bullish, but mid-term alignment is weakening."
        )
    elif long_state == "Bearish" and mid_state != "Bearish":
        sentences.append(
            "Higher-timeframe structure is bearish, though mid-term structure shows early divergence."
        )
    else:
        sentences.append(
            "Higher-timeframe structure is mixed, with no dominant directional control."
        )

    # Sentence 2: Local condition (balance + volatility + friction)
    local_notes = []

    if balance_state == "in_balance":
        local_notes.append("price is rotating within balance")
    elif balance_state == "breakout_up":
        local_notes.append("price is pressing above balance")
    elif balance_state == "breakdown_down":
        local_notes.append("price is slipping below balance")

    if touch_rank and "Fourth" in touch_rank:
        local_notes.append("structure shows signs of fatigue")

    if squeeze:
        local_notes.append("volatility is compressed and vulnerable to expansion")

    if friction == "High":
        local_notes.append("market friction is elevated")

    if local_notes:
        sentences.append(
            "Locally, " + ", and ".join(local_notes) + "."
        )

    return " ".join(sentences[:2])  # Hard limit: 2 sentences

def build_cross_asset_narrative(snapshot):
    """
    Synthesize cross-asset alignment into one authoritative paragraph.

    Answers: Do equities, vol, and risk proxies agree — or are they arguing?

    Returns: (narrative_text, confidence_level)
    """
    eq_states = []
    eq_frictions = []
    vol_state = None
    vol_friction = None

    for symbol, data in snapshot.items():
        if symbol == "VIX":
            vol_state = data.get("market_state")
            vol_friction = data.get("market_friction")
        elif symbol not in ["COMBINED"]:
            eq_states.append(data.get("market_state"))
            eq_frictions.append(data.get("market_friction"))

    # Count state alignment
    trending_count = eq_states.count("TRENDING")
    transition_count = eq_states.count("TRANSITION")
    range_count = eq_states.count("RANGE")
    stressed_count = eq_states.count("STRESSED")
    total = len(eq_states)

    # Narrative logic
    if trending_count >= total * 0.75:
        if vol_state != "STRESSED":
            narrative = (
                "Risk assets are aligned in trending regimes while volatility remains controlled. "
                "The market narrative is coherent."
            )
            confidence = "High"
        else:
            narrative = (
                "Risk assets are trending but volatility shows stress signals, signaling structural "
                "tension beneath the surface."
            )
            confidence = "Moderate"

    elif stressed_count >= total * 0.5:
        narrative = (
            "Multiple assets are showing structural stress. "
            "Defensive positioning is warranted across the complex."
        )
        confidence = "High"

    elif range_count >= total * 0.75:
        narrative = (
            "Cross-asset signals are contained in balance. No asset class is asserting control."
        )
        confidence = "Moderate"

    elif trending_count >= total * 0.5:
        high_friction = eq_frictions.count("High") >= total * 0.5
        if high_friction:
            narrative = (
                "Equities show trending bias across timeframes, but market friction "
                "is elevated. This divergence suggests rising sensitivity to headlines "
                "and flow-driven reversals."
            )
        else:
            narrative = (
                "Equities show trending bias with moderate cross-asset alignment. "
                "Narrative is constructive but not unanimous."
            )
        confidence = "Moderate"

    else:
        narrative = (
            "Cross-asset signals are diverging. Market narrative is unstable."
        )
        confidence = "Low"

    return narrative, confidence


def build_headline_context(result):
    """
    Generate supporting context sentence that explains the spine's tension/calm.

    This is NOT the main narrative (that's the spine).
    This explains WHY the spine feels stable or unstable.

    Max 1-2 sentences.
    """
    score = result.get("confluence_score", 0)
    friction = result.get("market_friction")
    technical = result.get("layers", {}).get("technical", {})
    balance_state = technical.get("structure", {}).get("balance_state")

    # Alignment assessment
    if score >= 9:
        alignment = "Alignment is strong"
    elif score >= 6:
        alignment = "Alignment is improving"
    else:
        alignment = "Alignment is thin"

    # Structure note
    structure_note = {
        "breakout_up": "with price pressing above balance",
        "breakdown_down": "with price slipping below balance",
        "in_balance": "with price contained in balance"
    }.get(balance_state, "with structure still forming")

    return f"{alignment} {structure_note}. Market friction is {friction.lower()}."


def build_headline_summary(result):
    """Legacy wrapper for build_headline_context(). Use build_headline_context() for new code."""
    return build_headline_context(result)

def generate_execution_plan(result):
    """Generate entry, stop, and target levels for optional planning"""
    
    current_price = result['current_price']
    
    # This will be filled in with actual logic from MA system and technical layers
    execution = {
        'entry_zone': current_price,  # Placeholder
        'stop_loss': current_price * 0.98,  # Placeholder
        'targets': [],  # Will be populated from sequence levels
        'position_size': None,  # Calculate from ATR
        'risk_reward': None
    }
    
    # Add next sequence levels as targets
    if 'sequence' in result['layers']:
        execution['targets'] = result['layers']['sequence'].get('next_magnets', [])
    
    return execution

def display_results(result):
    """Legacy entrypoint for full scan display."""
    render_symbol_analysis(result, {"primary_tf": "1D"})

def display_price_chart(result, chart_tf, chart_range):
    """Show price chart with overlays for the selected timeframe."""
    data = result.get('data', {}).get('timeframes', {}).get(chart_tf)
    if data is None or data.empty:
        data = result.get('data', {}).get('daily')
    if data is None or data.empty:
        st.info("Price chart not available (no price data loaded).")
        return

    data = filter_chart_data(data, chart_range)
    tech = TechnicalAnalyzer()
    balance = tech._analyze_balance_zones(data)
    balance_zone = balance.get('current_zone') or (balance.get('zones') or [None])[0]
    if balance_zone and balance_zone.get('mid') is None:
        low = balance_zone.get('low')
        high = balance_zone.get('high')
        balance_zone['mid'] = (low + high) / 2 if low is not None and high is not None else None

    events = build_event_markers(data)
    signal_markers = build_signal_markers(data, chart_tf)
    tf_label = TIMEFRAME_OPTIONS.get(chart_tf, {}).get("label", chart_tf)

    st.subheader("PRICE CHART")
    st.caption(f"Data status: Loaded | {tf_label} | Range: {chart_range}")
    fig = build_price_chart(data, balance_zone=balance_zone, events=events, signal_markers=signal_markers, title=None)
    st.plotly_chart(fig, use_container_width=True)

def display_market_memory_trace(result):
    """Display Market Memory Trace (formerly Signal Timeline)"""
    st.subheader("MARKET MEMORY TRACE")
    st.caption(
        "This is not a signal log. It is a behavioral record of similar market states. "
        "When the market looked like this before, what usually happened?"
    )

    timeline = build_market_memory_trace(result)
    if timeline.empty:
        st.caption("Data status: Loaded (no high-confluence clusters)")
        st.write("No high-confluence clusters were detected in the current windows.")
        return

    st.caption("Data status: Loaded | Multi-timeframe confluence | Outcomes shown since signal")

    # Color-code by resolution type
    def highlight_resolution(row):
        if row["Resolution Type"] == "Trend Continuation":
            return ['background-color: rgba(61, 220, 151, 0.1)'] * len(row)
        elif row["Resolution Type"] == "Mean Reversion":
            return ['background-color: rgba(246, 195, 67, 0.1)'] * len(row)
        elif row["Resolution Type"] == "Chop / Fade":
            return ['background-color: rgba(244, 91, 105, 0.1)'] * len(row)
        return [''] * len(row)

    st.dataframe(
        timeline.style.apply(highlight_resolution, axis=1),
        use_container_width=True,
        hide_index=True
    )


def display_signal_timeline(result):
    """Legacy wrapper for display_market_memory_trace()"""
    display_market_memory_trace(result)

def display_event_feed(result):
    """Display macro events, news, and filings."""
    st.subheader("EVENTS AND NEWS")

    ticker = result.get('ticker', 'N/A')
    api_key = resolve_alpha_key()

    if not api_key:
        st.caption("Data status: Partial (Alpha Vantage key missing)")
        st.write("Set ALPHAVANTAGE_API_KEY to enable Alpha Vantage feeds.")
    else:
        st.caption("Data status: Loaded (Alpha Vantage + free sources)")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Macro Releases (latest)**")
        if not api_key:
            st.write("Alpha Vantage key not configured.")
        else:
            macro_events = cached_macro_events(api_key)
            if not macro_events:
                st.write("No macro releases returned.")
            else:
                for item in macro_events:
                    date = item.get("timestamp").date() if item.get("timestamp") else "N/A"
                    value = item.get("value", "N/A")
                    st.write(f"- {item.get('title')} | {date} | {value}")

        st.write("**Market News**")
        if not api_key:
            st.write("Alpha Vantage key not configured.")
        else:
            market_news = cached_market_news(api_key)
            if not market_news:
                st.write("No market news returned.")
            else:
                for item in market_news[:6]:
                    title = item.get("title", "Untitled")
                    url = item.get("url")
                    source = item.get("source", "Source")
                    if url:
                        st.write(f"- [{title}]({url}) ({source})")
                    else:
                        st.write(f"- {title} ({source})")

    with col2:
        st.write(f"**{ticker} News and PR**")
        if not api_key:
            st.write("Alpha Vantage key not configured.")
        else:
            news = cached_alpha_news(ticker, api_key)
            if not news:
                st.write("No Alpha Vantage news returned.")
            else:
                for item in news[:6]:
                    title = item.get("title", "Untitled")
                    url = item.get("url")
                    source = item.get("source", "Source")
                    if url:
                        st.write(f"- [{title}]({url}) ({source})")
                    else:
                        st.write(f"- {title} ({source})")

        st.write("**Yahoo RSS (fallback)**")
        rss = cached_rss_news(ticker)
        if not rss:
            st.write("No RSS items returned.")
        else:
            for item in rss[:6]:
                title = item.get("title", "Untitled")
                url = item.get("url")
                if url:
                    st.write(f"- [{title}]({url})")
                else:
                    st.write(f"- {title}")

        st.write("**Recent SEC Filings**")
        filings = cached_sec_filings(ticker)
        if not filings:
            st.write("No filings returned.")
        else:
            for item in filings[:6]:
                date = item.get("timestamp").date() if item.get("timestamp") else "N/A"
                title = item.get("title", "Filing")
                summary = item.get("summary", "")
                st.write(f"- {date} | {title} {('- ' + summary) if summary else ''}")
def display_market_memory(result):
    """Display Market Memory analysis"""
    st.subheader("MARKET MEMORY (Proxies)")

    memory = result['layers'].get('market_memory', {})

    if not memory:
        st.info("Market Memory analysis not enabled.")
        return

    st.write(
        "This layer reads the market's background mood using proxies like breadth, ratios, and volatility."
    )

    breadth = memory.get('breadth', {})
    ratios = memory.get('ratios', {})
    vol = memory.get('volatility', {})

    breadth_loaded = any(item.get('value') is not None for item in breadth.values())
    ratios_loaded = any(item.get('value') is not None for item in ratios.values())
    vol_loaded = any(item.get('value') is not None for item in vol.values())

    loaded = []
    missing = []
    if breadth_loaded:
        loaded.append("breadth")
    else:
        missing.append("breadth")
    if ratios_loaded:
        loaded.append("ratios")
    else:
        missing.append("ratios")
    if vol_loaded:
        loaded.append("volatility")
    else:
        missing.append("volatility")

    coverage = []
    if loaded:
        coverage.append("Loaded: " + ", ".join(loaded))
    if missing:
        coverage.append("Missing: " + ", ".join(missing))
    status = "Not loaded"
    if loaded and missing:
        status = "Partial"
    elif loaded:
        status = "Loaded"

    if coverage:
        st.write("Data coverage: " + " | ".join(coverage))
    st.caption(f"Data status: {status}")

    zone_hit = memory.get('zone_hit', False)
    divergence = memory.get('divergence', False)

    if zone_hit and divergence:
        signal_text = "Background is stretched and out of sync, so reactions can be choppy."
    elif zone_hit:
        signal_text = "A known market memory zone is active. That can sharpen reactions."
    elif divergence:
        signal_text = "Proxies are drifting away from price, a sign of uneven participation."
    elif not (breadth_loaded or ratios_loaded or vol_loaded):
        signal_text = "Proxy data is missing, so this layer is limited."
    else:
        signal_text = "Proxies are calm right now with no strong warning flags."

    st.write(f"Signal: {signal_text}")

    # Display breadth zones
    st.write("**Breadth Indicators:**")
    for indicator, data in breadth.items():
        status = "Yes" if data.get('zone_hit') else "No"
        value = data.get('value')
        st.write(f"{status} - {indicator}: {value if value is not None else 'Not loaded'}")

    # Display ratio analysis
    st.write("**Intermarket Ratios:**")
    for ratio, data in ratios.items():
        status = "Yes" if data.get('memory_hit') else "No"
        value = data.get('value')
        st.write(f"{status} - {ratio}: {value if value is not None else 'Not loaded'}")

    # Display volatility
    st.write("**Volatility:**")
    for indicator, data in vol.items():
        status = "Yes" if data.get('extreme') else "No"
        value = data.get('value')
        st.write(f"{status} - {indicator}: {value if value is not None else 'Not loaded'}")

    # IMPACT and WEIGHT verdict
    st.divider()
    if zone_hit and divergence:
        impact = "Bearish"
        weight = "High"
    elif zone_hit or divergence:
        impact = "Neutral"
        weight = "Medium"
    else:
        impact = "Neutral"
        weight = "Low"

    st.write(f"**IMPACT:** {impact}")
    st.write(f"**WEIGHT:** {weight}")
def display_sequence_analysis(result):
    """Display Sequence Map analysis"""
    st.subheader("SEQUENCE MAP")

    sequence = result['layers'].get('sequence', {})

    if not sequence:
        st.caption("Data status: Not loaded")
        st.info("Sequence analysis not enabled")
        return

    st.write(
        "This layer maps price into repeating 100-point zones to highlight where attention pools."
    )
    st.caption("Data status: Loaded")

    is_holy = sequence.get('is_holy_trinity', False)
    is_palindrome = sequence.get('is_palindrome', False)
    is_oj_pivot = sequence.get('is_oj_pivot', False)
    magnets = sequence.get('next_magnets', [])

    flags = []
    if is_holy:
        flags.append("Holy Trinity level")
    if is_palindrome:
        flags.append("palindrome")
    if is_oj_pivot:
        flags.append("OJ pivot zone")

    # Current floor
    current_price = result['current_price']
    floor = sequence.get('current_floor', 'Unknown')
    floor_type = sequence.get('floor_type', '')

    if flags:
        signal_text = "Price is at a " + ", ".join(flags) + ", so attention is elevated."
    else:
        signal_text = "Price is between the biggest sequence levels right now."

    if floor_type and floor_type != "Unknown":
        signal_text += f" The floor is labeled '{floor_type}', which often draws focus."
        behavior = sequence.get('floor_behavior')
        if behavior:
            signal_text += f" Behavior note: {behavior}"

    if magnets:
        signal_text += " Next magnets are " + ", ".join(map(str, magnets)) + "."

    st.write(f"Signal: {signal_text}")

    st.metric("Current Price", f"${current_price:.2f}")
    st.metric("Floor Range", f"{floor} - {floor_type}")
    if sequence.get('sequence_score') is not None:
        st.metric("Sequence Score", sequence.get('sequence_score'))

    # Special levels
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Palindrome:** {'Yes' if is_palindrome else 'No'}")

    with col2:
        st.write(f"**Holy Trinity:** {'Yes' if is_holy else 'No'}")

    # OJ Pivot status
    oj_status = "Inside OJ Pivot" if is_oj_pivot else "Outside OJ Pivot"
    st.write(f"**OJ Pivot (62-69-77):** {oj_status}")

    # Next magnets
    if magnets:
        st.write(f"**Next Magnets:** {', '.join(map(str, magnets))}")

    # IMPACT and WEIGHT verdict
    st.divider()
    if is_holy and is_palindrome:
        impact = "Neutral"
        weight = "High"
    elif is_holy or is_palindrome or is_oj_pivot:
        impact = "Neutral"
        weight = "Medium"
    else:
        impact = "Neutral"
        weight = "Low"

    st.write(f"**IMPACT:** {impact}")
    st.write(f"**WEIGHT:** {weight}")

def display_balance_structure(result):
    """Display balance/imbalance zones with touch counts."""
    st.subheader("BALANCE STRUCTURE")
    data = result.get("data", {}).get("daily")
    if data is None or data.empty:
        st.caption("Data status: Not loaded")
        st.info("Balance structure not available.")
        return

    tech = TechnicalAnalyzer()
    balance = tech._analyze_balance_zones(data.tail(756))
    zone = select_balance_zone_near_price(data, result.get("current_price"), lookback_days=756)
    state = balance.get('balance_state', 'none')
    touch_counts = balance.get('touch_counts', {})
    touch_rank = balance.get('touch_rank')

    if not zone:
        st.caption("Data status: Loaded (no dominant balance zone detected)")
        st.write("Balance zones are still forming. Use structure and volume for context.")
        return

    st.caption("Data status: Loaded (recent balance zone)")
    st.write(f"Signal: Current state is **{state.replace('_', ' ')}**.")
    st.metric("Balance Zone", f"{zone.get('low', 0):.2f} - {zone.get('high', 0):.2f}")
    if zone.get('mid') is not None:
        st.write(f"Midpoint: {zone.get('mid'):.2f}")
    if zone.get('source'):
        st.caption(f"Zone source: {zone.get('source').replace('_', ' ')}")
    if touch_rank:
        st.write(f"Touch Rank: {touch_rank}")

    if touch_counts:
        st.write("**Touches**")
        st.write(f"All-time: {touch_counts.get('all_time', 0)}")
        st.write(f"This year: {touch_counts.get('year', 0)}")
        st.write(f"Last 90d: {touch_counts.get('90d', 0)}")
        st.write(f"This month: {touch_counts.get('30d', 0)}")
        st.caption("First touches are cleanest. Fourth+ touches often signal a break.")

    # IMPACT and WEIGHT verdict
    st.divider()
    if state == "breakout_up":
        impact = "Bullish"
        weight = "High" if touch_rank and "Fourth" in touch_rank else "Medium"
    elif state == "breakdown_down":
        impact = "Bearish"
        weight = "High" if touch_rank and "Fourth" in touch_rank else "Medium"
    elif state == "in_balance":
        impact = "Neutral"
        weight = "Medium"
    else:
        impact = "Neutral"
        weight = "Low"

    st.write(f"**IMPACT:** {impact}")
    st.write(f"**WEIGHT:** {weight}")

def display_technical_analysis(result):
    """Display Technical Analysis"""
    st.subheader("TECHNICAL CONFLUENCE")

    technical = result['layers'].get('technical', {})

    if not technical:
        st.caption("Data status: Not loaded")
        st.info("Technical analysis not enabled")
        return

    st.write(
        "This scans price action, candlesticks, structure, and volatility to gauge pressure."
    )
    status = "Loaded" if technical.get('patterns') or technical.get('structure') or technical.get('volume') else "Not loaded"
    st.caption(f"Data status: {status}")

    patterns = technical.get('patterns', {})
    candles = technical.get('candles', {})
    detected = [name.replace('_', ' ').title() for name, detected in patterns.items() if detected]
    candle_hits = [name.replace('_', ' ').title() for name, detected in candles.items() if detected]
    volume_climax = technical.get('volume', {}).get('climax_detected', False)
    structure = technical.get('structure', {})
    has_gaps = bool(structure.get('gaps'))
    trendline_touch = structure.get('trendline_touch', False)
    balance_state = structure.get('balance_state')
    bollinger_squeeze = technical.get('bollinger_squeeze', False)

    summary_bits = []
    if detected:
        summary_bits.append("Patterns showing: " + ", ".join(detected) + ".")
    if candle_hits:
        summary_bits.append("Candlestick pressure: " + ", ".join(candle_hits) + ".")
    if trendline_touch:
        summary_bits.append("Price is leaning on a trendline.")
    if balance_state and balance_state != "none":
        summary_bits.append(f"Balance state: {balance_state.replace('_', ' ')}.")
    if bollinger_squeeze:
        summary_bits.append("Bollinger squeeze is active; volatility expansion likely.")
    if has_gaps:
        summary_bits.append("Unfilled gaps and imbalance are still in play.")
    if volume_climax:
        summary_bits.append("Volume spiked, which can mark a turning point.")

    if summary_bits:
        signal_text = " ".join(summary_bits)
    else:
        signal_text = "No clear pattern or structure flag stands out right now."

    st.write(f"Signal: {signal_text}")

    # Patterns
    st.write("**Price Action Patterns:**")
    for pattern, is_detected in patterns.items():
        status = "Yes" if is_detected else "No"
        st.write(f"{status} - {pattern.upper().replace('_', ' ')}")

    st.write("**Candlesticks:**")
    for pattern, is_detected in candles.items():
        status = "Yes" if is_detected else "No"
        st.write(f"{status} - {pattern.upper().replace('_', ' ')}")

    # Structure
    st.write("**Market Structure:**")
    structure_flags = {
        "Trendline touch": structure.get("trendline_touch", False),
        "Imbalance present": structure.get("imbalance_present", False),
        "Balance state": structure.get("balance_state") not in [None, "none"]
    }
    gap_count = len(structure.get("gaps", [])) if structure.get("gaps") is not None else 0
    st.write(f"{'Yes' if gap_count else 'No'} - GAPS ({gap_count})")
    for label, present in structure_flags.items():
        status = "Yes" if present else "No"
        st.write(f"{status} - {label.upper()}")

    # IMPACT and WEIGHT verdict
    st.divider()
    bullish_signals = sum([1 for p in patterns.values() if p]) + sum([1 for c in candles.values() if c])
    if bollinger_squeeze or volume_climax:
        impact = "Bullish" if bullish_signals > 0 else "Bearish" if bullish_signals < 0 else "Neutral"
        weight = "High"
    elif detected or candle_hits:
        impact = "Neutral"
        weight = "Medium"
    else:
        impact = "Neutral"
        weight = "Low"

    st.write(f"**IMPACT:** {impact}")
    st.write(f"**WEIGHT:** {weight}")

def display_ma_system(result):
    """Display 10/50/200 MA System analysis"""
    st.subheader("10/50/200 MA SYSTEM")

    ma_system = result['layers'].get('ma_system', {})

    if not ma_system:
        st.caption("Data status: Not loaded")
        st.info("MA System not enabled")
        return

    st.write(
        "This is a daily trend compass using 10/50/200 SMAs. It reacts only when the bigger trend is clear."
    )
    sma200 = ma_system.get('sma200')
    if pd.isna(sma200):
        st.caption("Data status: Loaded (insufficient history for full regime)")
    else:
        st.caption("Data status: Loaded")

    regime = ma_system.get('regime', 'Unknown')
    signal = ma_system.get('signal', 'None')

    if signal in ['Long', 'Short']:
        signal_text = f"Regime is {regime}, and the system points {signal.lower()}."
    elif signal in ['Exit Long', 'Exit Short']:
        signal_text = f"The system suggests {signal.lower()}, which can mean momentum is fading."
    else:
        signal_text = f"Regime is {regime} with no fresh crossover right now."

    st.write(f"Signal: {signal_text}")

    regime_label = {
        'Bull': 'BULL',
        'Bear': 'BEAR',
        'Neutral': 'NEUTRAL'
    }.get(regime, 'UNKNOWN')

    st.metric("Current Regime", f"{regime_label} {regime}")

    # Signals
    st.write(f"**Active Signal:** {signal}")

    # Entry validity
    entry_valid = ma_system.get('entry_valid', False)
    st.write(f"**Entry Valid:** {'Yes' if entry_valid else 'No'}")

    # Exit status
    exit_triggered = ma_system.get('exit_triggered', False)
    if exit_triggered:
        st.warning("Exit condition triggered.")

    # IMPACT and WEIGHT verdict
    st.divider()
    if signal in ['Long']:
        impact = "Bullish"
        weight = "High" if entry_valid else "Medium"
    elif signal in ['Short']:
        impact = "Bearish"
        weight = "High" if entry_valid else "Medium"
    elif signal in ['Exit Long', 'Exit Short']:
        impact = "Neutral"
        weight = "Medium"
    else:
        impact = "Neutral"
        weight = "Low"

    st.write(f"**IMPACT:** {impact}")
    st.write(f"**WEIGHT:** {weight}")

def display_strategy_performance(result):
    """Display historical strategy performance"""
    st.subheader("STRATEGY PERFORMANCE")

    backtest = result['layers'].get('backtest', {})

    if not backtest:
        st.caption("Data status: Not loaded (backtesting disabled)")
        st.info("Backtesting not enabled")
        return

    st.write(
        f"Historical performance for {result['ticker']} is shown below. "
        "This is context for swing-quality setups, not a promise."
    )
    st.caption("Data status: Loaded")

    for strategy, perf in backtest.items():
        strategy_label = strategy.replace('_', ' ').title()
        with st.expander(f"{strategy_label}", expanded=False):
            summary = (
                f"This is the historical snapshot for the {strategy_label} style on {result['ticker']}. "
                "Use it to gauge how this approach has behaved over time."
            )
            st.write(summary)

            if perf.get('error'):
                signal_text = f"Data was incomplete for this strategy: {perf.get('error')}"
            else:
                total_trades = perf.get('total_trades', 0)
                win_rate = perf.get('win_rate', 0)
                avg_return = perf.get('avg_return', 0)

                if total_trades == 0:
                    signal_text = "Not enough trades to judge this style yet."
                elif win_rate >= 55 and avg_return > 0:
                    signal_text = "The past edge looks positive and fairly consistent."
                elif win_rate >= 50 and avg_return > 0:
                    signal_text = "The past edge looks mild; treat it as supportive context."
                else:
                    signal_text = "The edge looks mixed; lean on other layers for clarity."

            st.write(f"Signal: {signal_text}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Win Rate", f"{perf.get('win_rate', 0)}%")
                st.metric("Avg Return", f"{perf.get('avg_return', 0)}%")

            with col2:
                st.metric("Best TF", perf.get('best_timeframe', 'N/A'))
                st.metric("Trades", perf.get('total_trades', 0))
def display_timeframe_alignment(result, primary_tf="1D"):
    """Display multi-timeframe alignment."""
    st.subheader("TIMEFRAME ALIGNMENT")

    timeframes = result['layers'].get('timeframes', {})
    if not timeframes:
        st.caption("Data status: Not loaded")
        st.info("No timeframes analyzed")
        return

    st.write("Story alignment across selected timeframes.")
    st.caption("Data status: Loaded")

    for tf, data in timeframes.items():
        label = TIMEFRAME_OPTIONS.get(tf, {}).get("label", tf)
        title = f"{label} (primary)" if tf == primary_tf else label
        with st.expander(title, expanded=(tf == primary_tf)):
            if data.get('error'):
                st.write("Data status: Not loaded")
                st.write("Signal: No data was returned for this timeframe.")
                continue

            seq = data.get('sequence', {})
            if seq:
                st.write(f"**Floor:** {seq.get('current_floor', 'N/A')}")

            regime = data.get('ma_regime', 'Unknown')
            st.write(f"**MA Regime:** {regime}")

            tech = data.get('technical', {})
            signal_count = 0
            structure_flag = False
            balance_state = None
            if tech and isinstance(tech, dict):
                signal_count = tech.get('total_signals', 0)
                structure_flag = tech.get('structure_flags', False)
                balance_state = tech.get('balance_state')
                st.write(f"**Active Signals:** {signal_count}")

            st.write("Data status: Loaded")
            structure_note = " with structure imbalance" if structure_flag else ""
            if balance_state:
                structure_note += f" ({balance_state.replace('_', ' ')})"
            st.write(f"Signal: MA regime is {regime} with {signal_count} technical flags active{structure_note}.")

    # Timeframe Authority verdict
    st.divider()
    st.markdown("**TIMEFRAME AUTHORITY**")

    # Determine authority
    long_state = result.get("market_states", {}).get("long")
    mid_state = result.get("market_states", {}).get("mid")
    short_state = result.get("market_states", {}).get("short")

    if long_state == mid_state and long_state not in ["Choppy", "RANGE"]:
        verdict = "Daily and weekly structure dominate. Lower timeframes are subordinate."
    elif mid_state not in ["Choppy", "RANGE"] and short_state in ["Choppy", "RANGE"]:
        verdict = "Daily structure is leading while intraday structure remains noisy."
    elif short_state not in ["Choppy", "RANGE"] and mid_state in ["Choppy", "RANGE"]:
        verdict = "Intraday structure is leading while higher timeframes remain neutral."
    else:
        verdict = "No dominant timeframe. All horizons are contested."

    st.write(verdict)

def display_checklist(result):
    """Display the 12-point confluence checklist"""
    st.subheader("12-POINT CONFLUENCE CHECKLIST")
    st.write("Higher scores mean stronger alignment. This is analysis only.")
    st.caption("Half or more of the weighted checklist signals a higher-confluence zone.")

    checklist = result['checklist']

    # Create 3 columns for the checklist
    col1, col2, col3 = st.columns(3)

    items = list(checklist.items())

    with col1:
        for i in range(0, 4):
            if i < len(items):
                key, value = items[i]
                status = "Yes" if value else "No"
                st.write(f"{status} - {key.replace('_', ' ').title()}")

    with col2:
        for i in range(4, 8):
            if i < len(items):
                key, value = items[i]
                status = "Yes" if value else "No"
                st.write(f"{status} - {key.replace('_', ' ').title()}")

    with col3:
        for i in range(8, 12):
            if i < len(items):
                key, value = items[i]
                status = "Yes" if value else "No"
                st.write(f"{status} - {key.replace('_', ' ').title()}")
def display_execution_plan(result):
    """Display optional planning levels for context"""
    st.info("OPTIONAL PLANNING LEVELS (Context Only)")

    execution = result.get('execution', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        entry = execution.get('entry_zone', 'N/A')
        st.metric("Entry Zone", f"${entry:.2f}" if isinstance(entry, (int, float)) else entry)

    with col2:
        stop = execution.get('stop_loss', 'N/A')
        st.metric("Stop Loss", f"${stop:.2f}" if isinstance(stop, (int, float)) else stop)

    with col3:
        targets = execution.get('targets', [])
        if targets:
            target_str = f"${targets[0]:.2f}"
            st.metric("Target 1", target_str)
        else:
            st.metric("Target 1", "N/A")

    with col4:
        rr = execution.get('risk_reward', 'TBD')
        st.metric("Risk:Reward", rr)

    # Additional targets
    if len(targets) > 1:
        st.write(f"**Additional Targets:** {', '.join([f'${t:.2f}' for t in targets[1:]])}")

if __name__ == "__main__":
    main()
