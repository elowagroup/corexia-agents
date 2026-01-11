# COREXIA Agents

Autonomous trading agents powered by COREXIA Market Intelligence.

## Philosophy

This is not a signal bot.
This is not a black box.
This is a market cognition laboratory with memory, accountability, and internal disagreement.

COREXIA Agents consume the COREXIA Market Spine and make trading decisions through three distinct personalities:

- Steward - Conservative capital preservation
- Operator - Opportunistic transition trader
- Hunter - Aggressive volatility exploitation

All three see the same market intelligence. They differ only in interpretation and risk tolerance.

---

## Architecture

```
COREXIA Intelligence (matrix_scanner/)
  -> Market Spine + Regime Analysis
  -> Agent Decision Engine (corexia-agents/)
  -> Paper Broker (Sandbox)
  -> Supabase (Memory + Audit Trail)
  -> Observer Console (Streamlit, read only)
```

---

## Setup

### 1. Install Dependencies

```bash
cd corexia-agents
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Required:
- SUPABASE_URL - Your Supabase project URL
- SUPABASE_SERVICE_KEY - Service role key (backend only)
- COREXIA_PATH - Path to matrix_scanner directory

Optional (Observer Console):
- SUPABASE_ANON_KEY - Read-only key for the Streamlit console

Optional (Alpaca Paper Trading):
- ALPACA_API_KEY
- ALPACA_SECRET_KEY

### 3. Initialize Supabase Schema

Run the SQL from `app/supabase_client.py` in your Supabase SQL editor to create tables.

### 4. Initialize Agents

```bash
python -c "from app.supabase_client import init_agents; init_agents()"
```

---

## Usage

### Manual Run (Testing)

```bash
python app/worker.py
```

This runs one complete agent cycle for all three agents.

### API Server (Optional)

```bash
python app/main.py
```

Endpoints:
- GET / - Health check
- POST /run - Manually trigger agent run
- GET /status - Agent status summary
- GET /decisions/recent - Recent decisions

### Observer Console (Read Only)

```bash
streamlit run observer_console.py
```

The console never executes trades. It only reads Supabase logs and telemetry.

### Production (Cron)

Set up a daily cron job at market close (4:00 PM ET):

```cron
0 21 * * 1-5 cd /path/to/corexia-agents && python app/worker.py
```

---

## Safety Guarantees

1. Paper Only (Phase 1)
   - All agents start with $10,000 virtual capital
   - Minimum 60 trading days before any real money

2. Hard Stops
   - Max drawdown per agent (10-20%)
   - Daily loss limits (1-3%)
   - Max position sizes (15-35%)
   - Max concurrent positions (2-5)

3. Audit Trail
   - Every decision logged to Supabase
   - Every block reason recorded
   - Every position tracked
   - Full explainability

4. No Free Will
   - Agents cannot bypass drift/friction gates
   - Agents cannot exceed risk limits
   - Agents cannot hide losses
   - Agents cannot trade without logging

---

## Agent Profiles

### Steward (Conservative)
- Objective: Preserve capital, compound slowly
- Max Drawdown: 10%
- Daily Loss Limit: 1%
- Max Position: 15%
- Trades When: Friction = Low, State = TRENDING, Similarity >= 60%
- Philosophy: Do not lose money

### Operator (Opportunistic)
- Objective: Exploit regime transitions
- Max Drawdown: 15%
- Daily Loss Limit: 2%
- Max Position: 25%
- Trades When: State = TRANSITION, Volatility compressed, Similarity >= 50%
- Philosophy: Comfortable with uncertainty

### Hunter (Aggressive)
- Objective: Maximize return velocity
- Max Drawdown: 20%
- Daily Loss Limit: 3%
- Max Position: 35%
- Trades When: Volatility compressed or stressed, Similarity >= 40%
- Philosophy: Accepts chop as cost of business

---

## Decision Flow

```text
1. Pull Market Spine from COREXIA
2. Calculate Narrative Drift
3. Query Regime Similarity Stats
4. Interpret via Agent Personality
5. Propose Action (or abstain)
6. Apply Risk Gates
7. Execute Paper Trade (or block)
8. Log Everything to Supabase
9. Update Daily Performance
```

Every step is logged. Nothing is silent.

---

## Phase Progression

### Phase 1: Sandbox (Mandatory)
- 3 agents, $10k paper each
- 60+ trading days
- No real money
- Kill poorly-behaved agents

### Phase 2: Live Probe (Single Agent)
- $1-2k real capital
- One agent only (Steward or Operator)
- Hard stop at -10%
- Manual kill switch

### Phase 3: Parallel Reality
- 1 agent live, 3 agents paper
- Compare behavior
- Detect slippage, stress response

---

## What This Is Not

- Not a signal service
- Not a black box
- Not a set and forget system
- Not a shortcut

## What This Is

- A market cognition lab
- Explainable AI
- Memory-aware
- Behaviorally differentiated
- Auditable

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
  README.md
```

---

Built with discipline. Tested with rigor. Scaled with caution.
