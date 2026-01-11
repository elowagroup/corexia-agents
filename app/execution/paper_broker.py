"""
Paper Broker - No real money execution

Eventually will support Alpaca Paper Trading API
For now: simple in-memory simulation
"""
from datetime import datetime
from typing import Dict, Optional


class PaperBroker:
    """
    Paper trading broker.

    Phase 1: In-memory simulation
    Phase 2: Alpaca Paper API integration
    """

    def __init__(self):
        self.positions = {}  # symbol -> {side, size, entry_price, entry_time}
        self.orders = []

    def execute(self, trade: dict, current_price: float) -> dict:
        """
        Execute paper trade.

        Args:
            trade: {action, symbol, size_pct, rationale}
            current_price: current market price

        Returns:
            execution: {entry_price, status, timestamp}
        """
        symbol = trade["symbol"]
        action = trade["action"]
        size_pct = trade["size_pct"]

        execution = {
            "symbol": symbol,
            "side": action,
            "size_pct": size_pct,
            "entry_price": current_price,
            "status": "FILLED",
            "timestamp": datetime.now().isoformat(),
            "rationale": trade.get("rationale", "")
        }

        # Store position
        self.positions[symbol] = {
            "side": action,
            "size_pct": size_pct,
            "entry_price": current_price,
            "entry_time": datetime.now()
        }

        self.orders.append(execution)

        return execution

    def close_position(self, symbol: str, exit_price: float) -> dict:
        """Close existing position"""
        if symbol not in self.positions:
            raise ValueError(f"No open position for {symbol}")

        pos = self.positions[symbol]
        entry_price = pos["entry_price"]

        # Calculate P&L
        if pos["side"] == "LONG":
            pnl_pct = (exit_price - entry_price) / entry_price
        else:  # SHORT
            pnl_pct = (entry_price - exit_price) / entry_price

        exit_trade = {
            "symbol": symbol,
            "side": "CLOSE",
            "exit_price": exit_price,
            "pnl_pct": pnl_pct * 100,
            "timestamp": datetime.now().isoformat()
        }

        del self.positions[symbol]
        self.orders.append(exit_trade)

        return exit_trade

    def get_position(self, symbol: str) -> Optional[dict]:
        """Get current position for symbol"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> dict:
        """Get all open positions"""
        return self.positions.copy()


# Global broker instance (one per agent in production)
broker = PaperBroker()
