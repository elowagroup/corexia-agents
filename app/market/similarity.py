"""
Regime Similarity - queries historical regime archive
"""
from app.market.corexia_loader import load_corexia_modules


def get_similarity_stats(symbol: str, current_state: str, current_friction: str) -> dict:
    """
    Get regime similarity statistics from COREXIA archive.

    Returns:
    - total_occurrences: int
    - trend_continuation_pct: float
    - mean_reversion_pct: float
    - chop_pct: float
    - median_10d_return: float
    - confidence: float (0-1)
    """
    _, corexia_regime = load_corexia_modules()
    query_similar_regimes = corexia_regime.query_similar_regimes
    build_regime_summary = corexia_regime.build_regime_summary

    df = query_similar_regimes(symbol, current_state, current_friction, max_results=50)

    if df.empty:
        return {
            "total_occurrences": 0,
            "trend_continuation_pct": 0.0,
            "mean_reversion_pct": 0.0,
            "chop_pct": 0.0,
            "median_10d_return": 0.0,
            "confidence": 0.0
        }

    summary = build_regime_summary(df)
    if not summary:
        return {
            "total_occurrences": 0,
            "confidence": 0.0
        }

    # Confidence = occurrences / 50 (capped at 1.0)
    confidence = min(summary["total_occurrences"] / 50, 1.0)

    return {
        **summary,
        "confidence": confidence
    }
