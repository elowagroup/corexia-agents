"""
Configuration management for COREXIA Agents
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Alpaca
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").lower() == "true"

# COREXIA
COREXIA_PATH = Path(os.getenv("COREXIA_PATH", "matrix_scanner"))

# Capital
CAPITAL_START = float(os.getenv("CAPITAL_START", "10000"))

# Agent Profiles
STEWARD_PROFILE = {
    "name": "Steward",
    "objective": "Preserve capital, compound slowly",
    "max_drawdown_pct": 0.10,
    "daily_loss_limit_pct": 0.01,
    "max_position_pct": 0.15,
    "max_positions": 2,
    "allowed_friction": ["Low", "Moderate"],
    "allowed_drift": ["None", "Minor"],
    "regime_preference": ["TRENDING"],
    "trade_conditions": {
        "similarity_threshold": 0.60,
        "require_memory_support": True,
        "avoid_balance": True
    },
    "cooldown_after_losses": None
}

OPERATOR_PROFILE = {
    "name": "Operator",
    "objective": "Exploit regime transitions",
    "max_drawdown_pct": 0.15,
    "daily_loss_limit_pct": 0.02,
    "max_position_pct": 0.25,
    "max_positions": 4,
    "allowed_friction": ["Low", "Moderate"],
    "allowed_drift": ["None", "Minor", "Moderate"],
    "regime_preference": ["TRANSITION", "TRENDING"],
    "trade_conditions": {
        "similarity_threshold": 0.50,
        "require_vol_compression": True,
        "allow_balance_if_breaking": True
    },
    "cooldown_after_losses": 2
}

HUNTER_PROFILE = {
    "name": "Hunter",
    "objective": "Maximize return velocity",
    "max_drawdown_pct": 0.20,
    "daily_loss_limit_pct": 0.03,
    "max_position_pct": 0.35,
    "max_positions": 5,
    "allowed_friction": ["Low", "Moderate", "High"],
    "allowed_drift": ["None", "Minor", "Moderate", "Major"],
    "regime_preference": ["STRESSED", "TRANSITION"],
    "trade_conditions": {
        "similarity_threshold": 0.40,
        "allow_disagreement": True,
        "size_down_in_major_drift": True
    },
    "cooldown_after_losses": 3
}
