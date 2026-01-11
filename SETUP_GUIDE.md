# COREXIA Agents - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd corexia-agents
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# REQUIRED: Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# OPTIONAL: Observer Console (read only)
SUPABASE_ANON_KEY=your-anon-key

# REQUIRED: COREXIA Integration
COREXIA_PATH=matrix_scanner

# OPTIONAL: Alpaca Paper Trading (for future Phase 2)
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_PAPER=true

# Agent Config
CAPITAL_START=10000

# Agent Schedule (ET default)
COREXIA_TZ=America/New_York
COREXIA_RUN_TIMES=09:30,10:30,11:30,14:30,15:30
COREXIA_RUN_MODE=schedule

# Admin Console
COREXIA_ADMIN_USER=admin
COREXIA_ADMIN_PASSWORD=your_password
```

### 3. Set Up Supabase Database

Option A: SQL Editor (Recommended)

1. Go to your Supabase project SQL Editor
2. Open `app/supabase_client.py`
3. Copy the `SCHEMA_SQL` string
4. Paste into Supabase SQL editor
5. Run the SQL

Option B: View Schema

The schema creates these tables:
- market_regime_archive - Daily market spine snapshots
- agents - Agent profiles
- agent_decisions - Every decision (including blocks)
- agent_positions - Position tracking
- agent_performance_daily - Daily equity tracking

### 4. Initialize Agent Records

```bash
python -c "from app.supabase_client import init_agents; init_agents()"
```

This creates 3 agent records in Supabase:
- Steward - Conservative (10% max drawdown)
- Operator - Opportunistic (15% max drawdown)
- Hunter - Aggressive (20% max drawdown)

### 5. Verify Setup

```bash
python test_imports.py
```

You should see:
```
[OK] Config loaded
[OK] Agent classes loaded
[OK] Execution layer loaded
[OK] Logging utilities loaded
```

---

## Running Agents

### Manual Test Run

```bash
python -m app.worker
```

This runs one complete cycle for all 3 agents:
1. Pull Market Spine from COREXIA
2. Calculate Narrative Drift
3. Query Regime Similarity
4. Each agent interprets market
5. Makes decision (or abstains)
6. Risk checks enforced
7. Paper trade executed (or blocked)
8. Everything logged to Supabase

### Example Output

```
============================================================
Running Steward agent cycle at 2026-01-10 16:00:00
============================================================
Building market context from COREXIA...
Calculating narrative drift...
Querying regime similarity...

Market State: TRENDING
Market Friction: Low
Narrative Drift: STABLE
Similarity Confidence: 75%
Market Spine: Higher-timeframe structure remains bullish...

[ALLOWED] Allowed to trade. Analyzing...

[DECISION] LONG SPY 15.0%
   Rationale: Trending bullish with 75% historical support

[EXECUTING] Risk check passed. Executing...

[EXECUTED]
   LONG SPY @ $450.25
   Size: 15.0%

============================================================
Steward cycle complete
============================================================
```

---

## Observer Console

### Launch the Dashboard

```bash
streamlit run observer_console.py
```

The console is read only. It never executes trades.

---

## Production Deployment

### Cron Setup (Daily at Market Close)

Add to your crontab:

```bash
# Run agents daily at 4:00 PM ET (21:00 UTC)
0 21 * * 1-5 cd /path/to/corexia-agents && python -m app.worker >> logs/agent_runs.log 2>&1
```

### API Server (Optional)

```bash
python app/main.py
```

Then access:
- http://localhost:8000/ - Health check
- POST http://localhost:8000/run - Manual trigger
- GET http://localhost:8000/status - Agent status
- GET http://localhost:8000/decisions/recent - Recent decisions

---

## Monitoring

### Check Agent Status

```sql
-- In Supabase SQL Editor
SELECT
    a.name,
    apd.date,
    apd.equity,
    apd.daily_pnl,
    apd.drawdown,
    apd.exposure_pct
FROM agent_performance_daily apd
JOIN agents a ON a.id = apd.agent_id
ORDER BY apd.date DESC, a.name
LIMIT 30;
```

### Check Recent Decisions

```sql
SELECT
    a.name,
    ad.timestamp,
    ad.proposed_action,
    ad.blocked_reason,
    ad.confidence,
    ad.interpretation
FROM agent_decisions ad
JOIN agents a ON a.id = ad.agent_id
ORDER BY ad.timestamp DESC
LIMIT 20;
```

### Check Open Positions

```sql
SELECT
    a.name,
    ap.symbol,
    ap.side,
    ap.size_pct,
    ap.entry_price,
    ap.opened_at,
    ap.rationale
FROM agent_positions ap
JOIN agents a ON a.id = ap.agent_id
WHERE ap.closed_at IS NULL
ORDER BY ap.opened_at DESC;
```

---

## Troubleshooting

### Import Errors

Error: No module named 'supabase'
Fix: pip install -r requirements.txt

### COREXIA Integration Errors

Error: Could not import COREXIA modules
Fix:
1. Verify COREXIA_PATH in .env points to the local matrix_scanner directory
2. Check COREXIA is set up:
   `cd ../matrix_scanner && python -c "from app import run_corexia_scan; print('OK')"`

### Supabase Connection Errors

Error: Invalid API key
Fix:
1. Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
2. Use Service Role Key, not anon key (Supabase Settings -> API)

### Agent Not Trading

Check decision logs in Supabase. Common block reasons:
- Narrative drift blocked: MAJOR DRIFT
- Market friction blocked: High
- Historical support insufficient: 45%
- State not trending: RANGE

This is expected. Agents are designed to sit in cash frequently.

---

## Safety Checks

Before any real money (Phase 2):

- Minimum 60 trading days of paper trading
- All 3 agents show positive Sharpe ratio
- Max drawdown stayed below profile limits
- Decision logs show clear rationales
- No unexplained losses
- Agent can explain worst loss calmly

Never graduate an agent to real money unless all checks pass.

---

## Agent Personalities

### Steward (Conservative)
- Only trades TRENDING markets
- Requires 60%+ similarity confidence
- Max position: 15%
- Blocks: High friction, Major drift
- Philosophy: Do not lose money

### Operator (Opportunistic)
- Trades TRANSITION and TRENDING
- Requires 50%+ similarity confidence
- Max position: 25%
- Allows moderate drift
- Philosophy: Comfortable with uncertainty

### Hunter (Aggressive)
- Trades STRESSED and TRANSITION
- Requires 40%+ similarity confidence
- Max position: 35%
- Allows all friction levels
- Philosophy: Accepts chop as cost of business

---

## Next Steps

1. Run 60-day sandbox: let agents trade paper for 2-3 months
2. Review weekly: check decision logs and equity curves
3. Identify best agent: which one handles stress best
4. Graduate one agent: move to $1-2k live capital (Phase 2)
5. Parallel reality: run 1 live, 3 paper (compare behavior)

---

## File Structure

```
corexia-agents/
  app/
    main.py
    worker.py
    config.py
    supabase_client.py
    market/
      corexia_loader.py
      spine.py
      similarity.py
    agents/
      base.py
      steward.py
      operator.py
      hunter.py
    execution/
      paper_broker.py
      risk.py
    logging/
      decisions.py
      performance.py
  observer_console.py
  requirements.txt
  .env.example
  test_imports.py
  README.md
```

---

Built with discipline. Tested with rigor. Scaled with caution.
