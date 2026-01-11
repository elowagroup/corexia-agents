"""
Decision Logging - Every thought is recorded
"""
from app.supabase_client import supabase


def log_decision(decision: dict):
    """
    Log agent decision to Supabase.

    Required fields:
    - agent_id
    - timestamp
    - market_spine
    - interpretation
    - intent
    - proposed_action
    - confidence
    - blocked_reason (optional)
    """
    try:
        supabase.table("agent_decisions").insert(decision).execute()
    except Exception as e:
        print(f"Warning: Failed to log decision: {e}")
