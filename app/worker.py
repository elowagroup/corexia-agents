"""
Agent Worker Loop - THE HEART

This runs on a schedule (cron) and executes the agent decision cycle.

NO UI DEPENDENCY. Ever.
"""
from datetime import datetime

from app.config import STEWARD_PROFILE, OPERATOR_PROFILE, HUNTER_PROFILE, CAPITAL_START
from app.supabase_client import supabase, get_agent_id
from app.market.spine import build_market_context, calculate_drift
from app.market.similarity import get_similarity_stats
from app.agents.steward import StewardAgent
from app.agents.operator import OperatorAgent
from app.agents.hunter import HunterAgent
from app.execution.paper_broker import broker
from app.execution.risk import risk_check
from app.logging.decisions import log_decision
from app.logging.performance import update_daily_performance


def run_agent_cycle(agent_class, profile: dict, symbol: str = "SPY"):
    """
    Run one agent decision cycle.

    Steps:
    1. Pull Market Spine
    2. Check Narrative Drift
    3. Get Similarity Stats
    4. Interpret via Agent
    5. Make Decision
    6. Apply Risk Checks
    7. Execute (or block)
    8. Log Everything
    """
    agent_name = profile["name"]
    agent_id = get_agent_id(agent_name)

    print(f"\n{'='*60}")
    print(f"Running {agent_name} agent cycle at {datetime.now()}")
    print(f"{'='*60}")

    # Step 1: Build Market Context
    print("Building market context from COREXIA...")
    market = build_market_context(symbol)

    # Step 2: Calculate Drift
    print("Calculating narrative drift...")
    drift = calculate_drift(symbol, market)
    market["drift"] = drift

    # Step 3: Get Similarity
    print("Querying regime similarity...")
    similarity = get_similarity_stats(
        symbol,
        market.get("state"),
        market.get("friction")
    )

    spine_preview = (market.get("spine") or "")[:100]
    print(f"\nMarket State: {market.get('state')}")
    print(f"Market Friction: {market.get('friction')}")
    print(f"Narrative Drift: {drift}")
    print(f"Similarity Confidence: {similarity.get('confidence', 0):.0%}")
    print(f"Market Spine: {spine_preview}...")

    # Step 4: Initialize Agent
    agent = agent_class(profile)

    # Step 5: Check if allowed to trade
    allowed, block_reason = agent.allowed(market)

    decision_log = {
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "market_spine": market.get("spine"),
        "interpretation": agent.interpret(market, similarity),
        "blocked_reason": block_reason,
        "symbol": symbol
    }

    if not allowed:
        print(f"\n[BLOCKED] {block_reason}")
        decision_log["intent"] = "Blocked by drift/friction gate"
        decision_log["proposed_action"] = None
        decision_log["confidence"] = 0.0
        log_decision(decision_log)
        return

    # Step 6: Make Decision
    print("\n[ALLOWED] Allowed to trade. Analyzing...")
    decision, decision_block = agent.decide(market, similarity)

    if decision_block:
        print(f"\n[DECISION BLOCKED] {decision_block}")
        decision_log["intent"] = "Blocked by decision logic"
        decision_log["proposed_action"] = decision_block
        decision_log["confidence"] = similarity.get("confidence", 0)
        log_decision(decision_log)
        return

    if not decision:
        print("\n[ABSTAIN] Agent chose to stay flat")
        decision_log["intent"] = "Abstained"
        decision_log["proposed_action"] = "FLAT"
        decision_log["confidence"] = similarity.get("confidence", 0)
        log_decision(decision_log)
        return

    # Step 7: Risk Check
    print(
        f"\n[DECISION] {decision['action']} {decision['symbol']} "
        f"{decision['size_pct']:.1%}"
    )
    print(f"   Rationale: {decision['rationale']}")

    risk_ok, risk_reason = risk_check(profile, agent_id, decision)

    if not risk_ok:
        print(f"\n[RISK BLOCKED] {risk_reason}")
        decision_log["intent"] = decision["rationale"]
        decision_log["proposed_action"] = f"{decision['action']} {decision['symbol']}"
        decision_log["confidence"] = decision.get("confidence", 0)
        decision_log["blocked_reason"] = risk_reason
        decision_log["size_pct"] = decision["size_pct"]
        log_decision(decision_log)
        return

    # Step 8: Execute
    print("\n[EXECUTING] Risk check passed. Executing...")
    current_price = market["current_price"]
    execution = broker.execute(decision, current_price)

    print("\n[EXECUTED]")
    print(f"   {execution['side']} {execution['symbol']} @ ${execution['entry_price']:.2f}")
    print(f"   Size: {execution['size_pct']:.1%}")

    # Step 9: Log Decision + Position
    decision_log["intent"] = decision["rationale"]
    decision_log["proposed_action"] = f"{decision['action']} {decision['symbol']}"
    decision_log["confidence"] = decision.get("confidence", 0)
    decision_log["size_pct"] = decision["size_pct"]
    log_decision(decision_log)

    # Log position in Supabase
    supabase.table("agent_positions").insert({
        "agent_id": agent_id,
        "symbol": execution["symbol"],
        "side": execution["side"],
        "size_pct": execution["size_pct"],
        "entry_price": execution["entry_price"],
        "rationale": decision["rationale"]
    }).execute()

    # Step 10: Update Performance
    update_daily_performance(agent_id, CAPITAL_START)

    print(f"\n{'='*60}")
    print(f"{agent_name} cycle complete")
    print(f"{'='*60}\n")


def run_daily():
    """
    Run daily agent loop for all agents.

    Called by cron at market close.
    """
    print("\n" + "="*60)
    print("DAILY AGENT RUN")
    print(f"Timestamp: {datetime.now()}")
    print("="*60 + "\n")

    # Run each agent
    for agent_class, profile in [
        (StewardAgent, STEWARD_PROFILE),
        (OperatorAgent, OPERATOR_PROFILE),
        (HunterAgent, HUNTER_PROFILE)
    ]:
        try:
            run_agent_cycle(agent_class, profile)
        except Exception as e:
            print(f"\n[ERROR] {profile['name']} cycle: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("DAILY RUN COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    # For testing: run manually
    run_daily()
