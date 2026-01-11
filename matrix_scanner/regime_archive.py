"""
Market Regime Archive - Historical Spine Memory

Stores daily snapshots of market spines and tracks outcomes.
This is not backtesting. It's state memory.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json

ARCHIVE_DIR = Path("data/regime_archive")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def store_regime_snapshot(symbol, snapshot):
    """
    Store one daily regime snapshot.

    Each row = one daily snapshot:
    - date, market_spine, market_state, market_friction
    - confluence_band, balance_state, volatility_state
    - forward returns (added later)
    """
    # Append to ticker's archive file
    archive_file = ARCHIVE_DIR / f"{symbol}_archive.jsonl"
    with open(archive_file, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


def classify_confluence_band(score):
    """Map confluence score to band."""
    if score >= 9:
        return "High"
    elif score >= 6:
        return "Medium"
    else:
        return "Low"


def classify_volatility_state(result):
    """Classify volatility state."""
    technical = result.get("layers", {}).get("technical", {})
    if technical.get("bollinger_squeeze"):
        return "Compressed"
    return "Normal"


def classify_htf_alignment(result):
    """Classify higher timeframe alignment."""
    horizons = result.get("market_states", {})
    long_state = horizons.get("long")
    mid_state = horizons.get("mid")

    if long_state == mid_state and long_state in ["Bullish", "Bearish"]:
        return "Aligned"
    elif long_state != mid_state:
        return "Conflicted"
    else:
        return "Neutral"


def load_regime_archive(symbol):
    """Load regime archive for a symbol."""
    archive_file = ARCHIVE_DIR / f"{symbol}_archive.jsonl"
    if not archive_file.exists():
        return pd.DataFrame()

    snapshots = []
    with open(archive_file, "r") as f:
        for line in f:
            snapshots.append(json.loads(line))

    return pd.DataFrame(snapshots)


def update_forward_returns(symbol):
    """
    Update forward returns for past snapshots.

    Run this daily to backfill outcomes.
    """
    archive_file = ARCHIVE_DIR / f"{symbol}_archive.jsonl"
    if not archive_file.exists():
        return

    # Load all snapshots
    snapshots = []
    with open(archive_file, "r") as f:
        for line in f:
            snapshots.append(json.loads(line))

    # For each snapshot without forward returns, try to calculate
    # (This requires fetching price data - implementation depends on data source)
    # Placeholder logic:
    # for snapshot in snapshots:
    #     if snapshot["forward_5d_return"] is None:
    #         # Fetch price 5 days later
    #         # Calculate return
    #         # Update snapshot
    #         pass

    # Write updated snapshots back
    # with open(archive_file, "w") as f:
    #     for snapshot in snapshots:
    #         f.write(json.dumps(snapshot) + "\n")


def query_similar_regimes(symbol, current_state, current_friction, max_results=50):
    """
    Query archive for similar regime states.

    Returns: DataFrame of past occurrences with outcomes.
    """
    archive_file = ARCHIVE_DIR / f"{symbol}_archive.jsonl"
    if not archive_file.exists():
        return pd.DataFrame()

    snapshots = []
    with open(archive_file, "r") as f:
        for line in f:
            snapshots.append(json.loads(line))

    # Filter for similar states
    similar = [
        s for s in snapshots
        if s.get("market_state") == current_state
        and s.get("market_friction") == current_friction
        and s.get("forward_10d_return") is not None  # Only complete records
    ]

    if not similar:
        return pd.DataFrame()

    df = pd.DataFrame(similar[-max_results:])  # Last N occurrences
    return df


def build_regime_summary(df):
    """
    Summarize regime query results.

    Returns: dict with statistics
    """
    if df.empty:
        return None

    total = len(df)

    # Count resolution types
    trend_count = (df["resolution_type"] == "Trend Continuation").sum()
    mean_reversion_count = (df["resolution_type"] == "Mean Reversion").sum()
    chop_count = (df["resolution_type"] == "Chop").sum()

    # Calculate median return
    median_return = df["forward_10d_return"].median()

    return {
        "total_occurrences": total,
        "trend_continuation_pct": round(trend_count / total * 100, 1),
        "mean_reversion_pct": round(mean_reversion_count / total * 100, 1),
        "chop_pct": round(chop_count / total * 100, 1),
        "median_10d_return": round(median_return, 2)
    }


def generate_regime_fingerprint(result):
    """
    Generate categorical fingerprint for regime matching.

    This is deterministic and explainable - no ML black boxes.
    """
    from technical_analysis import TechnicalAnalyzer

    data = result.get("data", {}).get("daily")
    touch_rank = None
    if data is not None and not data.empty:
        tech = TechnicalAnalyzer()
        balance = tech._analyze_balance_zones(data.tail(756))
        touch_rank = balance.get('touch_rank')

    return {
        "market_state": result.get("market_state"),
        "market_friction": result.get("market_friction"),
        "confluence_band": classify_confluence_band(result.get("confluence_score", 0)),
        "balance_state": result.get("layers", {}).get("technical", {}).get("structure", {}).get("balance_state"),
        "touch_rank": touch_rank,
        "volatility_state": classify_volatility_state(result),
        "htf_alignment": classify_htf_alignment(result)
    }


def daily_snapshot_job(symbols=["SPY", "QQQ", "IWM", "DIA", "VIX"]):
    """
    Run once per day at market close.
    Captures regime state for all macro symbols.

    This should be called by a cron job or scheduler.
    """
    from app import run_corexia_scan, build_market_spine

    for symbol in symbols:
        try:
            # Run scan
            result = run_corexia_scan(
                ticker=symbol,
                lookback_days=7300,
                timeframes={"1W": True, "1D": True, "4H": True},
                layers={
                    "market_memory": True,
                    "regime": True,
                    "sequence": True,
                    "ma_system": True,
                    "technical": True,
                    "backtest": False
                },
                primary_tf="1D",
                fast=True
            )

            # Build spine and snapshot
            spine = build_market_spine(result)
            fingerprint = generate_regime_fingerprint(result)

            snapshot = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "symbol": symbol,
                "market_spine": spine,
                "market_state": result.get("market_state"),
                "direction_bias": result.get("direction_bias"),
                "market_friction": result.get("market_friction"),
                "confluence_band": classify_confluence_band(result.get("confluence_score", 0)),
                "balance_state": fingerprint.get("balance_state"),
                "touch_rank": fingerprint.get("touch_rank"),
                "volatility_state": fingerprint.get("volatility_state"),
                "htf_alignment": fingerprint.get("htf_alignment"),
                "current_price": result.get("current_price"),
                "forward_5d_return": None,
                "forward_10d_return": None,
                "resolution_type": None,
                "created_at": datetime.now().isoformat()
            }

            # Store snapshot
            store_regime_snapshot(symbol, snapshot)

        except Exception as e:
            print(f"Snapshot failed for {symbol}: {e}")


def detect_narrative_drift(today_snapshot, yesterday_snapshot):
    """
    Detect semantic regime shifts by comparing categorical states.

    This is drift detection, not noise.

    Returns: (drift_level, changes_list)
    """
    changes = []

    # Compare critical regime dimensions
    if today_snapshot.get("market_state") != yesterday_snapshot.get("market_state"):
        changes.append((
            "State shift",
            f"{yesterday_snapshot.get('market_state')} → {today_snapshot.get('market_state')}"
        ))

    if today_snapshot.get("market_friction") != yesterday_snapshot.get("market_friction"):
        changes.append((
            "Friction change",
            f"{yesterday_snapshot.get('market_friction')} → {today_snapshot.get('market_friction')}"
        ))

    if today_snapshot.get("balance_state") != yesterday_snapshot.get("balance_state"):
        changes.append((
            "Structure change",
            f"{yesterday_snapshot.get('balance_state')} → {today_snapshot.get('balance_state')}"
        ))

    if today_snapshot.get("volatility_state") != yesterday_snapshot.get("volatility_state"):
        changes.append((
            "Volatility regime change",
            f"{yesterday_snapshot.get('volatility_state')} → {today_snapshot.get('volatility_state')}"
        ))

    # Classify drift severity
    if len(changes) >= 3:
        return "MAJOR DRIFT", changes
    elif len(changes) == 2:
        return "MODERATE DRIFT", changes
    elif len(changes) == 1:
        return "MINOR DRIFT", changes
    else:
        return "STABLE", []
