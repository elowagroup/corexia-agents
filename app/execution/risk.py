"""
Risk Enforcement - HARD STOPS

No agent can bypass these constraints.
"""
from typing import Tuple
from datetime import datetime, timedelta
from app.supabase_client import supabase


def risk_check(agent_profile: dict, agent_id: str, trade: dict) -> Tuple[bool, str]:
    """
    Check if trade passes risk constraints.

    Hard stops:
    - Max position size
    - Max drawdown
    - Daily loss limit
    - Max open positions
    - Cooldown after losses

    Returns: (allowed, reason)
    """
    # Position size check
    if trade["size_pct"] > agent_profile["max_position_pct"]:
        return False, f"Position size {trade['size_pct']:.1%} exceeds max {agent_profile['max_position_pct']:.1%}"

    # Check max open positions
    positions = supabase.table("agent_positions")\
        .select("*")\
        .eq("agent_id", agent_id)\
        .is_("closed_at", "null")\
        .execute()

    if len(positions.data) >= agent_profile["max_positions"]:
        return False, f"Max positions reached: {len(positions.data)}/{agent_profile['max_positions']}"

    # Check drawdown
    today = datetime.now().strftime("%Y-%m-%d")
    perf = supabase.table("agent_performance_daily")\
        .select("*")\
        .eq("agent_id", agent_id)\
        .eq("date", today)\
        .execute()

    if perf.data and perf.data[0].get("drawdown", 0) >= agent_profile["max_drawdown_pct"]:
        return False, f"Max drawdown breached: {perf.data[0]['drawdown']:.1%}"

    # Check daily loss limit
    if perf.data and perf.data[0].get("daily_pnl", 0) <= -agent_profile["daily_loss_limit_pct"]:
        return False, f"Daily loss limit hit: {perf.data[0]['daily_pnl']:.1%}"

    # Check loss cooldown
    cooldown = agent_profile.get("cooldown_after_losses")
    if cooldown:
        # Get recent losing trades
        recent_trades = supabase.table("agent_positions")\
            .select("*")\
            .eq("agent_id", agent_id)\
            .not_.is_("closed_at", "null")\
            .order("closed_at", desc=True)\
            .limit(cooldown)\
            .execute()

        if len(recent_trades.data) >= cooldown:
            all_losses = all(t.get("pnl", 0) < 0 for t in recent_trades.data)
            if all_losses:
                return False, f"Cooldown active after {cooldown} consecutive losses"

    return True, "Passed"


def check_account_health(agent_id: str, capital_start: float) -> dict:
    """
    Check overall account health.

    Returns:
    - current_equity: float
    - drawdown: float
    - status: OK | WARNING | CRITICAL
    """
    today = datetime.now().strftime("%Y-%m-%d")
    perf = supabase.table("agent_performance_daily")\
        .select("*")\
        .eq("agent_id", agent_id)\
        .order("date", desc=True)\
        .limit(1)\
        .execute()

    if not perf.data:
        return {
            "current_equity": capital_start,
            "drawdown": 0.0,
            "status": "OK"
        }

    equity = perf.data[0].get("equity", capital_start)
    drawdown = perf.data[0].get("drawdown", 0)

    if drawdown >= 0.15:
        status = "CRITICAL"
    elif drawdown >= 0.10:
        status = "WARNING"
    else:
        status = "OK"

    return {
        "current_equity": equity,
        "drawdown": drawdown,
        "status": status
    }
