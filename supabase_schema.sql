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
