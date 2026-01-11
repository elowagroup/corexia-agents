"""
Market Spine Builder - imports COREXIA analysis
"""
from datetime import datetime, timedelta

from app.market.corexia_loader import load_corexia_modules


def build_market_context(symbol: str = "SPY") -> dict:
    """
    Run COREXIA scan and build market context.

    Returns dict with:
    - spine: narrative spine
    - state: market state (TRENDING/TRANSITION/RANGE/STRESSED)
    - friction: market friction
    - drift: narrative drift level
    - similarity: regime similarity stats
    - fingerprint: regime fingerprint
    """
    corexia_app, corexia_regime = load_corexia_modules()
    run_corexia_scan = corexia_app.run_corexia_scan
    build_market_spine = corexia_app.build_market_spine
    generate_regime_fingerprint = corexia_regime.generate_regime_fingerprint
    classify_confluence_band = corexia_regime.classify_confluence_band

    # Run COREXIA scan
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

    # Build spine
    spine = build_market_spine(result)

    # Get fingerprint
    fingerprint = generate_regime_fingerprint(result)

    # Build context
    context = {
        "spine": spine,
        "state": result.get("market_state"),
        "friction": result.get("market_friction"),
        "bias": result.get("direction_bias"),
        "confluence_score": result.get("confluence_score", 0),
        "confluence_band": classify_confluence_band(result.get("confluence_score", 0)),
        "balance_state": fingerprint.get("balance_state"),
        "volatility_state": fingerprint.get("volatility_state"),
        "htf_alignment": fingerprint.get("htf_alignment"),
        "current_price": result.get("current_price"),
        "fingerprint": fingerprint,
        "drift": "None",  # Will be calculated if historical data exists
        "raw_result": result  # For agent interpretation
    }

    return context


def calculate_drift(symbol: str, today_context: dict) -> str:
    """
    Calculate narrative drift by comparing to yesterday's snapshot.

    Returns: "STABLE" | "MINOR DRIFT" | "MODERATE DRIFT" | "MAJOR DRIFT"
    """
    from app.supabase_client import supabase

    _, corexia_regime = load_corexia_modules()
    detect_narrative_drift = corexia_regime.detect_narrative_drift

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    result = supabase.table("market_regime_archive")\
        .select("*")\
        .eq("symbol", symbol)\
        .eq("date", yesterday)\
        .execute()

    if not result.data:
        return "None"

    yesterday_snapshot = result.data[0]
    today_snapshot = {
        "market_state": today_context["state"],
        "market_friction": today_context["friction"],
        "balance_state": today_context["balance_state"],
        "volatility_state": today_context["volatility_state"]
    }

    drift_level, _ = detect_narrative_drift(today_snapshot, yesterday_snapshot)
    return drift_level
