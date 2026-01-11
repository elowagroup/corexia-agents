"""
Operator Agent - Opportunistic Transition Trader
"""
from app.agents.base import Agent
from typing import Tuple, Optional, Dict


class OperatorAgent(Agent):
    """
    The Operator: Exploits regime transitions.

    Philosophy:
    - Comfortable with uncertainty
    - Trades when structure is forming
    - Trusts compression + similarity
    - Accepts whipsaws
    """

    def interpret(self, market: dict, similarity: dict) -> str:
        """Operator interpretation"""
        state = market.get("state")
        volatility = market.get("volatility_state")
        confidence = similarity.get("confidence", 0)

        if state == "TRANSITION":
            return "Regime shift detected - transition opportunity available"

        if volatility == "Compressed" and state != "RANGE":
            return "Volatility compression with directional structure - expansion likely"

        if state == "TRENDING" and confidence >= 0.5:
            return "Early trend with historical precedent - opportunistic entry"

        if state == "STRESSED":
            return "Volatility elevated - waiting for regime clarity"

        return "No transition signal active"

    def decide(self, market: dict, similarity: dict) -> Tuple[Optional[dict], Optional[str]]:
        """
        Operator decision logic.

        Trades when:
        - State = TRANSITION or early TRENDING
        - Volatility compressed OR expanding
        - Similarity >= 50%
        """
        state = market.get("state")
        volatility = market.get("volatility_state")
        bias = market.get("bias")
        confidence = similarity.get("confidence", 0)
        balance_state = market.get("balance_state")

        # Similarity threshold
        if confidence < self.profile["trade_conditions"]["similarity_threshold"]:
            return None, f"Similarity below threshold: {confidence:.1%}"

        # State requirements: TRANSITION or TRENDING
        if state not in ["TRANSITION", "TRENDING"]:
            # Special case: breakout from balance
            if self.profile["trade_conditions"].get("allow_balance_if_breaking"):
                if balance_state in ["breakout_up", "breakdown_down"]:
                    pass  # Allow
                else:
                    return None, f"State not suitable: {state}"
            else:
                return None, f"State not suitable: {state}"

        # Volatility check
        if self.profile["trade_conditions"].get("require_vol_compression"):
            if volatility not in ["Compressed", "Expanding"]:
                return None, f"Volatility state not compressed: {volatility}"

        # Determine direction
        if bias not in ["Bullish", "Bearish"]:
            return None, "Directional bias unclear"

        side = "LONG" if bias == "Bullish" else "SHORT"
        size = self.size_position(market, self.profile["max_position_pct"])

        decision = {
            "action": side,
            "symbol": "SPY",
            "size_pct": size,
            "rationale": f"Transition {bias.lower()} with {volatility} volatility",
            "confidence": confidence
        }

        return decision, None
