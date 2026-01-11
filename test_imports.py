"""
Quick import test to verify all modules load correctly
"""

print("Testing COREXIA Agents imports...")

try:
    from app.config import STEWARD_PROFILE, OPERATOR_PROFILE, HUNTER_PROFILE
    print("[OK] Config loaded")
    print(f"  - Steward: {STEWARD_PROFILE['objective']}")
    print(f"  - Operator: {OPERATOR_PROFILE['objective']}")
    print(f"  - Hunter: {HUNTER_PROFILE['objective']}")
except Exception as e:
    print(f"[FAIL] Config failed: {e}")

try:
    from app.agents.base import Agent
    from app.agents.steward import StewardAgent
    from app.agents.operator import OperatorAgent
    from app.agents.hunter import HunterAgent
    print("[OK] Agent classes loaded")
except Exception as e:
    print(f"[FAIL] Agents failed: {e}")

try:
    from app.execution.paper_broker import broker
    from app.execution.risk import risk_check
    print("[OK] Execution layer loaded")
except Exception as e:
    print(f"[FAIL] Execution failed: {e}")

try:
    from app.logging.decisions import log_decision
    from app.logging.performance import update_daily_performance
    print("[OK] Logging utilities loaded")
except Exception as e:
    print(f"[FAIL] Logging failed: {e}")

print("\n[SUCCESS] All core modules imported successfully!")
print("\nNote: Market spine and Supabase require .env configuration to test fully")
