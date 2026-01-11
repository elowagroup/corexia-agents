"""
COREXIA Agents - System Check

Comprehensive verification of setup and configuration.
"""
import os
import sys
from pathlib import Path

print("="*60)
print("COREXIA AGENTS - SYSTEM CHECK")
print("="*60)

# Check 1: Python Version
print("\n[1/7] Python Version")
version = sys.version_info
if version.major >= 3 and version.minor >= 8:
    print(f"    [OK] Python {version.major}.{version.minor}.{version.micro}")
else:
    print(f"    [WARN] Python {version.major}.{version.minor} - recommend 3.8+")

# Check 2: Directory Structure
print("\n[2/7] Directory Structure")
required_dirs = [
    "app/market",
    "app/agents",
    "app/execution",
    "app/logging",
    "data"
]
all_dirs_ok = True
for dir_path in required_dirs:
    if Path(dir_path).exists():
        print(f"    [OK] {dir_path}/")
    else:
        print(f"    [FAIL] {dir_path}/ missing")
        all_dirs_ok = False

# Check 3: Core Files
print("\n[3/7] Core Files")
required_files = [
    "app/config.py",
    "app/worker.py",
    "app/main.py",
    "app/supabase_client.py",
    "app/market/spine.py",
    "app/market/corexia_loader.py",
    "app/market/similarity.py",
    "app/agents/base.py",
    "app/agents/steward.py",
    "app/agents/operator.py",
    "app/agents/hunter.py",
    "app/execution/paper_broker.py",
    "app/execution/risk.py",
    "app/logging/decisions.py",
    "app/logging/performance.py",
    "requirements.txt",
    ".env.example"
]
all_files_ok = True
for file_path in required_files:
    if Path(file_path).exists():
        print(f"    [OK] {file_path}")
    else:
        print(f"    [FAIL] {file_path} missing")
        all_files_ok = False

# Check 4: Environment Configuration
print("\n[4/7] Environment Configuration")
if Path(".env").exists():
    print("    [OK] .env file exists")
    from dotenv import load_dotenv
    load_dotenv()

    # Check critical env vars
    env_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
        "COREXIA_PATH": os.getenv("COREXIA_PATH"),
        "CAPITAL_START": os.getenv("CAPITAL_START", "10000")
    }

    for var, value in env_vars.items():
        if value and value != "your_supabase_url" and value != "your_service_key":
            print(f"    [OK] {var} configured")
        else:
            print(f"    [WARN] {var} not configured (check .env)")
else:
    print("    [WARN] .env file not found (copy from .env.example)")

# Check 5: COREXIA Integration
print("\n[5/7] COREXIA Integration")
corexia_path = Path(os.getenv("COREXIA_PATH", "../matrix_scanner"))
if corexia_path.exists():
    print(f"    [OK] COREXIA path exists: {corexia_path}")

    # Check for key COREXIA files
    key_files = ["app.py", "regime_archive.py"]
    for file in key_files:
        if (corexia_path / file).exists():
            print(f"    [OK] {file} found")
        else:
            print(f"    [WARN] {file} not found in COREXIA")
else:
    print(f"    [FAIL] COREXIA path not found: {corexia_path}")
    print("          Set COREXIA_PATH in .env to matrix_scanner directory")

# Check 6: Python Dependencies
print("\n[6/7] Python Dependencies")
dependencies = {
    "fastapi": "FastAPI",
    "uvicorn": "Uvicorn",
    "supabase": "Supabase",
    "dotenv": "python-dotenv",
    "pandas": "Pandas",
    "numpy": "NumPy"
}

missing = []
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"    [OK] {name}")
    except ImportError:
        print(f"    [FAIL] {name} - run: pip install -r requirements.txt")
        missing.append(name)

# Check 7: Agent Profiles
print("\n[7/7] Agent Profiles")
try:
    from app.config import STEWARD_PROFILE, OPERATOR_PROFILE, HUNTER_PROFILE
    print("    [OK] Agent profiles loaded")
    print(f"         - Steward: {STEWARD_PROFILE['max_drawdown_pct']:.0%} max drawdown")
    print(f"         - Operator: {OPERATOR_PROFILE['max_drawdown_pct']:.0%} max drawdown")
    print(f"         - Hunter: {HUNTER_PROFILE['max_drawdown_pct']:.0%} max drawdown")
except Exception as e:
    print(f"    [FAIL] Could not load agent profiles: {e}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if all_dirs_ok and all_files_ok:
    print("[OK] File structure complete")
else:
    print("[FAIL] File structure incomplete")

if Path(".env").exists():
    print("[OK] Environment configured")
else:
    print("[TODO] Create .env from .env.example")

if not missing:
    print("[OK] All dependencies installed")
else:
    print(f"[TODO] Install missing: {', '.join(missing)}")

if corexia_path.exists():
    print("[OK] COREXIA integration ready")
else:
    print("[TODO] Configure COREXIA_PATH in .env")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)

if missing:
    print("1. Install dependencies: pip install -r requirements.txt")

if not Path(".env").exists():
    print("2. Configure environment: cp .env.example .env && nano .env")
    print("3. Set up Supabase database (see SETUP_GUIDE.md)")
    print("4. Initialize agents: python -c 'from app.supabase_client import init_agents; init_agents()'")

if not missing and Path(".env").exists():
    print("1. Set up Supabase database (see SETUP_GUIDE.md)")
    print("2. Initialize agents: python -c 'from app.supabase_client import init_agents; init_agents()'")
    print("3. Test run: python app/worker.py")

print("="*60)
