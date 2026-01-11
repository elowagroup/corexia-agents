"""
Steward Agent - Conservative Capital Preservation
"""
from app.agents.base import Agent
from typing import Tuple, Optional, Dict


class StewardAgent(Agent):
    """
    The Steward: Conservative capital preservation.

    Philosophy:
    - Do not lose money
    - Hates friction
    - Needs confirmation + memory support
    - Sits in cash a lot
    """

    def interpret(self, market: dict, similarity: dict) -> str:
        """Steward interpretation of market conditions"""
        state = market.get("state")
        friction = market.get("friction")
        confidence = similarity.get("confidence", 0)

        if friction == "High":
            return "Environment too hostile for capital deployment"

        if state == "RANGE":
            return "Waiting for directional control to establish"

        if state == "TRENDING" and confidence >= 0.6:
            return "Stable regime with historical support - conditions acceptable"

        if state == "TRANSITION":
            return "Regime forming - premature to commit capital"

        if state == "STRESSED":
            return "Structural tension elevated - defensive posture required"

        return "No clear advantage detected"

    def decide(self, market: dict, similarity: dict) -> Tuple[Optional[dict], Optional[str]]:
        """
        Steward decision logic.

        Only trades when:
        - Friction = Low or Moderate
        - State = TRENDING
        - Similarity confidence >= 60%
        - Trend continuation favored
        """
        state = market.get("state")
        friction = market.get("friction")
        bias = market.get("bias")
        confidence = similarity.get("confidence", 0)
        trend_pct = similarity.get("trend_continuation_pct", 0)

        # Similarity threshold
        if confidence < self.profile["trade_conditions"]["similarity_threshold"]:
            return None, f"Historical support insufficient: {confidence:.1%}"

        # State requirements
        if state != "TRENDING":
            return None, f"State not trending: {state}"

        # Must favor trend continuation
        if trend_pct < 50:
            return None, f"Trend continuation weak: {trend_pct}%"

        # Determine direction
        if bias not in ["Bullish", "Bearish"]:
            return None, "Directional bias unclear"

        side = "LONG" if bias == "Bullish" else "SHORT"
        size = self.size_position(market, self.profile["max_position_pct"])

        decision = {
            "action": side,
            "symbol": "SPY",  # Steward only trades SPY
            "size_pct": size,
            "rationale": f"Trending {bias.lower()} with {confidence:.0%} historical support",
            "confidence": confidence
        }

        return decision, None
