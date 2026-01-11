"""
Supabase client and schema utilities
"""
from supabase import create_client, Client
from supabase.client import ClientOptions
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

# Initialize Supabase client
options = ClientOptions(
    schema="public",
    auto_refresh_token=False,
    persist_session=False,
    postgrest_client_timeout=30,
    storage_client_timeout=30
)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY, options=options)


# Schema creation SQL (run once manually in Supabase SQL editor)
SCHEMA_SQL = """
-- Market Regime Archive
CREATE TABLE IF NOT EXISTS market_regime_archive (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    market_spine TEXT,
    market_state TEXT,
    market_friction TEXT,
    confluence_band TEXT,
    balance_state TEXT,
    touch_rank TEXT,
    volatility_state TEXT,
    htf_alignment TEXT,
    cross_asset_narrative TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, symbol)
);

-- Agents
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    risk_profile TEXT,
    max_drawdown_pct FLOAT,
    max_position_pct FLOAT,
    volatility_tolerance TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Decisions
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    market_spine TEXT,
    interpretation TEXT,
    intent TEXT,
    proposed_action TEXT,
    confidence FLOAT,
    blocked_reason TEXT,
    symbol TEXT,
    size_pct FLOAT
);

-- Agent Positions
CREATE TABLE IF NOT EXISTS agent_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    size_pct FLOAT,
    entry_price FLOAT,
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    exit_price FLOAT,
    pnl FLOAT,
    rationale TEXT
);

-- Agent Performance Daily
CREATE TABLE IF NOT EXISTS agent_performance_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    date DATE NOT NULL,
    equity FLOAT,
    daily_pnl FLOAT,
    drawdown FLOAT,
    exposure_pct FLOAT,
    UNIQUE(agent_id, date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_regime_date ON market_regime_archive(date DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON agent_decisions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_positions_agent ON agent_positions(agent_id);
CREATE INDEX IF NOT EXISTS idx_performance_date ON agent_performance_daily(date DESC);
"""


def init_agents():
    """Initialize agent records in database"""
    from app.config import STEWARD_PROFILE, OPERATOR_PROFILE, HUNTER_PROFILE

    for profile in [STEWARD_PROFILE, OPERATOR_PROFILE, HUNTER_PROFILE]:
        try:
            supabase.table("agents").upsert({
                "name": profile["name"],
                "risk_profile": profile["objective"],
                "max_drawdown_pct": profile["max_drawdown_pct"],
                "max_position_pct": profile["max_position_pct"],
                "volatility_tolerance": ",".join(profile["allowed_friction"])
            }, on_conflict="name").execute()
        except Exception as e:
            print(f"Agent init warning for {profile['name']}: {e}")


def get_agent_id(agent_name: str) -> str:
    """Get agent UUID by name"""
    result = supabase.table("agents").select("id").eq("name", agent_name).execute()
    if result.data:
        return result.data[0]["id"]
    raise ValueError(f"Agent {agent_name} not found")
