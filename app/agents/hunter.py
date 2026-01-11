"""
Hunter Agent - Aggressive Return Maximization
"""
from typing import Tuple, Optional, Dict

from app.agents.base import Agent


class HunterAgent(Agent):
    """
    The Hunter: Maximizes return velocity.

    Philosophy:
    - Loves compression to expansion
    - Accepts chop as cost
    - Operates where others freeze
    - Tight stops, frequent turnover
    """

    def interpret(self, market: dict, similarity: dict) -> str:
        """Hunter interpretation"""
        state = market.get("state")
        volatility = market.get("volatility_state")
        friction = market.get("friction")

        if volatility == "Compressed":
            return "Volatility compressed - opportunity for fast directional move"

        if state == "STRESSED":
            return "Structural tension - high volatility environment active"

        if state == "TRANSITION" and friction == "High":
            return "Chaos in formation - acceptable operating environment"

        if state == "TRENDING":
            return "Trend established - momentum play available"

        return "Low volatility environment - reduced opportunity"

    def decide(self, market: dict, similarity: dict) -> Tuple[Optional[dict], Optional[str]]:
        """
        Hunter decision logic.

        Trades when:
        - Volatility compressed OR state = STRESSED
        - ANY similarity >= 40%
        - Accepts high friction
        - Sizes down in Major Drift
        """
        state = market.get("state")
        volatility = market.get("volatility_state")
        bias = market.get("bias")
        confidence = similarity.get("confidence", 0)

        # Similarity threshold (lowest of all agents)
        if confidence < self.profile["trade_conditions"]["similarity_threshold"]:
            return None, f"Even Hunter requires minimum similarity: {confidence:.1%}"

        # Volatility preference
        volatility_trigger = (
            volatility == "Compressed" or
            state == "STRESSED" or
            state == "TRANSITION"
        )

        if not volatility_trigger:
            return None, f"Volatility state not suitable for Hunter: {volatility}"

        # Direction (Hunter can trade neutral environments aggressively)
        if bias == "Neutral" and state != "STRESSED":
            return None, "No directional bias in non-stressed environment"

        side = "LONG" if bias == "Bullish" else "SHORT" if bias == "Bearish" else "FLAT"
        if side == "FLAT":
            return None, "No directional conviction"

        size = self.size_position(market, self.profile["max_position_pct"])

        decision = {
            "action": side,
            "symbol": "SPY",
            "size_pct": size,
            "rationale": f"Volatility play {bias.lower()} in {state} regime",
            "confidence": confidence
        }

        return decision, None
