"""
Base Agent Class - NO FREE WILL
"""
from typing import Tuple, Optional, Dict


class Agent:
    """
    Base agent class with hard constraints.

    All agents:
    - See the same COREXIA Market Spine
    - Respect the same risk gates
    - Differ only in interpretation + expression
    """

    def __init__(self, profile: dict):
        self.profile = profile
        self.name = profile["name"]

    def allowed(self, market: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if agent is allowed to trade in current market conditions.

        This is a HARD GATE. No agent can bypass this.

        Returns: (allowed, block_reason)
        """
        # Check drift
        drift = market.get("drift", "None")
        if drift not in self.profile["allowed_drift"]:
            return False, f"Narrative drift blocked: {drift}"

        # Check friction
        friction = market.get("friction")
        if friction not in self.profile["allowed_friction"]:
            return False, f"Market friction blocked: {friction}"

        return True, None

    def interpret(self, market: dict, similarity: dict) -> str:
        """
        Interpret market conditions through agent's lens.

        This is WHERE personalities diverge.
        """
        raise NotImplementedError("Subclass must implement interpret()")

    def decide(self, market: dict, similarity: dict) -> Tuple[Optional[dict], Optional[str]]:
        """
        Make trading decision.

        Returns: (decision, block_reason)
        - decision: dict with action, symbol, size_pct, rationale
        - block_reason: str if blocked
        """
        raise NotImplementedError("Subclass must implement decide()")

    def size_position(self, market: dict, base_size: float) -> float:
        """
        Adjust position size based on market conditions.

        All agents can size down, never up.
        """
        size = base_size

        # Size down in major drift (if profile allows)
        if market.get("drift") == "MAJOR DRIFT":
            if self.profile["trade_conditions"].get("size_down_in_major_drift"):
                size *= 0.5

        # Size down in high friction
        if market.get("friction") == "High":
            size *= 0.7

        # Never exceed profile max
        return min(size, self.profile["max_position_pct"])
