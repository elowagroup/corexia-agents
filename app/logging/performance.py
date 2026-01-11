"""
Performance Tracking - Daily equity snapshots
"""
from datetime import datetime
from app.supabase_client import supabase
from app.execution.paper_broker import broker


def update_daily_performance(agent_id: str, capital_start: float):
    """
    Update daily performance metrics for agent.

    Calculates:
    - Current equity
    - Daily P&L
    - Drawdown
    - Exposure
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Get all positions for agent
    positions_result = supabase.table("agent_positions")\
        .select("*")\
        .eq("agent_id", agent_id)\
        .execute()

    # Calculate equity
    total_pnl = 0
    exposure_pct = 0

    for pos in positions_result.data:
        if pos.get("closed_at"):
            # Closed position
            total_pnl += pos.get("pnl", 0) or 0
        else:
            # Open position
            exposure_pct += pos.get("size_pct", 0) or 0
            # TODO: calculate unrealized P&L when we have live prices

    equity = capital_start + (capital_start * total_pnl / 100)

    # Calculate drawdown
    peak_equity = equity  # Simplified - should track historical peak
    drawdown = max(0, (peak_equity - equity) / peak_equity) if peak_equity > 0 else 0

    # Get yesterday's equity for daily P&L
    yesterday_result = supabase.table("agent_performance_daily")\
        .select("equity")\
        .eq("agent_id", agent_id)\
        .order("date", desc=True)\
        .limit(1)\
        .execute()

    yesterday_equity = yesterday_result.data[0]["equity"] if yesterday_result.data else capital_start
    daily_pnl = ((equity - yesterday_equity) / yesterday_equity) if yesterday_equity > 0 else 0

    # Upsert today's performance
    perf_data = {
        "agent_id": agent_id,
        "date": today,
        "equity": equity,
        "daily_pnl": daily_pnl,
        "drawdown": drawdown,
        "exposure_pct": exposure_pct
    }

    try:
        supabase.table("agent_performance_daily")\
            .upsert(perf_data, on_conflict="agent_id,date")\
            .execute()
    except Exception as e:
        print(f"Warning: Failed to update performance: {e}")
