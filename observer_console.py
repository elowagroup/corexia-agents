"""
COREXIA Observer Console (Read-Only)

This dashboard reads from Supabase and never executes trades.
"""
from datetime import datetime
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

try:
    from supabase import create_client
except Exception:  # pragma: no cover - streamlit runtime only
    create_client = None


load_dotenv()

st.set_page_config(
    page_title="COREXIA Observer",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg: #f6f4ef;
  --panel: #ffffff;
  --ink: #121212;
  --muted: #6b6b6b;
  --accent: #0f766e;
  --accent-2: #f59e0b;
  --danger: #dc2626;
  --border: #e2e0da;
}

html, body, [class*="stApp"] {
  background: var(--bg);
  color: var(--ink);
  font-family: 'Space Grotesk', sans-serif;
}

h1, h2, h3 {
  letter-spacing: -0.02em;
}

.block-container {
  padding-top: 2rem;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.card-title {
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 6px;
}

.card-value {
  font-size: 1.6rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.card-sub {
  color: var(--muted);
  font-size: 0.9rem;
}

.pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent);
  font-weight: 600;
}

.pill.warn {
  background: rgba(245, 158, 11, 0.14);
  color: var(--accent-2);
}

.pill.danger {
  background: rgba(220, 38, 38, 0.12);
  color: var(--danger);
}

.hero {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hero-title {
  font-size: 2.2rem;
  font-weight: 700;
}

.hero-sub {
  color: var(--muted);
  font-size: 1rem;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.95rem;
  margin-top: 6px;
  color: var(--muted);
}

.stButton > button {
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--ink);
  font-weight: 600;
}

.stButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="hero">
  <div class="hero-title">COREXIA Observer</div>
  <div class="hero-sub">Read-only market cognition and agent telemetry.</div>
</div>
    """,
    unsafe_allow_html=True
)


if create_client is None:
    st.error("Supabase client not available. Install dependencies: pip install -r requirements.txt")
    st.stop()


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    key = anon_key or service_key
    if anon_key and not anon_key.startswith("eyJ"):
        # Supabase publishable keys are not supported by this client.
        key = service_key
    if not url or not key:
        return None, "Missing SUPABASE_URL or SUPABASE_ANON_KEY/SUPABASE_SERVICE_KEY"
    try:
        return create_client(url, key), None
    except Exception as exc:
        return None, str(exc)


supabase, supabase_error = get_supabase_client()
if supabase_error:
    st.error(f"Supabase not configured: {supabase_error}")
    st.stop()


@st.cache_data(ttl=60)
def fetch_agents():
    return supabase.table("agents").select("*").execute().data


@st.cache_data(ttl=60)
def fetch_latest_regime(symbol: str):
    result = supabase.table("market_regime_archive")\
        .select("*")\
        .eq("symbol", symbol)\
        .order("date", desc=True)\
        .limit(1)\
        .execute()
    return result.data[0] if result.data else None


@st.cache_data(ttl=60)
def fetch_recent_decisions(limit: int = 40):
    result = supabase.table("agent_decisions")\
        .select("*, agents(name)")\
        .order("timestamp", desc=True)\
        .limit(limit)\
        .execute()
    return result.data


@st.cache_data(ttl=60)
def fetch_open_positions():
    result = supabase.table("agent_positions")\
        .select("*")\
        .is_("closed_at", "null")\
        .order("opened_at", desc=True)\
        .execute()
    return result.data


@st.cache_data(ttl=60)
def fetch_performance():
    result = supabase.table("agent_performance_daily")\
        .select("*")\
        .order("date", desc=False)\
        .limit(2000)\
        .execute()
    return result.data


def format_money(value):
    if value is None:
        return "n/a"
    return f"${value:,.0f}"


def format_pct(value):
    if value is None:
        return "n/a"
    return f"{value:.1%}"


controls = st.columns([2, 1, 1, 1])
with controls[0]:
    symbol = st.selectbox("Market Snapshot", ["SPY", "QQQ", "IWM", "DIA", "VIX"], index=0)
with controls[1]:
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()
with controls[2]:
    st.caption(f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')} local")
with controls[3]:
    st.caption("Source: Supabase")


agents = fetch_agents()
agent_map = {agent["id"]: agent["name"] for agent in agents} if agents else {}


st.markdown("### Live Market Context")
market = fetch_latest_regime(symbol)

if market:
    cols = st.columns(4)
    cols[0].markdown(
        f"<div class='card'><div class='card-title'>Market State</div>"
        f"<div class='card-value'>{market.get('market_state', 'n/a')}</div>"
        f"<div class='card-sub'>Friction: {market.get('market_friction', 'n/a')}</div></div>",
        unsafe_allow_html=True
    )
    cols[1].markdown(
        f"<div class='card'><div class='card-title'>Confluence Band</div>"
        f"<div class='card-value'>{market.get('confluence_band', 'n/a')}</div>"
        f"<div class='card-sub'>Balance: {market.get('balance_state', 'n/a')}</div></div>",
        unsafe_allow_html=True
    )
    cols[2].markdown(
        f"<div class='card'><div class='card-title'>Volatility</div>"
        f"<div class='card-value'>{market.get('volatility_state', 'n/a')}</div>"
        f"<div class='card-sub'>HTF: {market.get('htf_alignment', 'n/a')}</div></div>",
        unsafe_allow_html=True
    )
    cols[3].markdown(
        f"<div class='card'><div class='card-title'>Snapshot Date</div>"
        f"<div class='card-value'>{market.get('date', 'n/a')}</div>"
        f"<div class='card-sub'>{symbol} spine stored</div></div>",
        unsafe_allow_html=True
    )
    st.markdown("#### Market Spine")
    st.info(market.get("market_spine") or "No market spine recorded yet.")
else:
    st.warning("No market regime snapshots yet. Run the agent worker to populate the archive.")


st.markdown("### Agent Status")

positions = fetch_open_positions()
positions_by_agent = {}
for position in positions:
    positions_by_agent.setdefault(position["agent_id"], []).append(position)

perf = fetch_performance()
perf_df = pd.DataFrame(perf)
latest_perf = {}
if not perf_df.empty:
    perf_df["date"] = pd.to_datetime(perf_df["date"])
    latest = perf_df.sort_values("date").groupby("agent_id").tail(1)
    for _, row in latest.iterrows():
        latest_perf[row["agent_id"]] = row.to_dict()

recent_decisions = fetch_recent_decisions()
last_decision_by_agent = {}
for decision in recent_decisions:
    agent_name = None
    agent_info = decision.get("agents")
    if isinstance(agent_info, dict):
        agent_name = agent_info.get("name")
    if not agent_name:
        agent_name = agent_map.get(decision.get("agent_id"), "Unknown")
    if agent_name not in last_decision_by_agent:
        last_decision_by_agent[agent_name] = decision

if not agents:
    st.warning("No agents found in Supabase. Run init_agents to seed the agents table.")
else:
    agent_cols = st.columns(len(agents))
    for col, agent in zip(agent_cols, agents):
        agent_id = agent["id"]
        agent_name = agent["name"]
        agent_positions = positions_by_agent.get(agent_id, [])
        sides = {p.get("side") for p in agent_positions}
        if not agent_positions:
            status = "Flat"
            pill_class = "pill"
        elif len(sides) == 1:
            side = list(sides)[0]
            status = "Long" if side == "LONG" else "Short"
            pill_class = "pill"
        else:
            status = "Mixed"
            pill_class = "pill warn"

        perf_row = latest_perf.get(agent_id, {})
        equity = format_money(perf_row.get("equity"))
        drawdown = format_pct(perf_row.get("drawdown"))

        last_decision = last_decision_by_agent.get(agent_name, {})
        proposed = last_decision.get("proposed_action") or "No action"
        blocked = last_decision.get("blocked_reason")
        decision_note = blocked if blocked else proposed

        col.markdown(
            f"<div class='card'>"
            f"<div class='card-title'>{agent_name}</div>"
            f"<div class='card-value'>{equity}</div>"
            f"<div class='{pill_class}'>{status}</div>"
            f"<div class='metric-row'><span>Drawdown</span><span>{drawdown}</span></div>"
            f"<div class='metric-row'><span>Open positions</span><span>{len(agent_positions)}</span></div>"
            f"<div class='metric-row'><span>Last decision</span><span>{decision_note}</span></div>"
            f"</div>",
            unsafe_allow_html=True
        )


st.markdown("### Equity Curves")
if perf_df.empty:
    st.info("No performance data yet. The worker will populate this table after runs.")
else:
    perf_df["agent"] = perf_df["agent_id"].map(agent_map)
    equity_pivot = perf_df.pivot(index="date", columns="agent", values="equity")
    st.line_chart(equity_pivot, use_container_width=True)


st.markdown("### Open Positions")
if not positions:
    st.info("No open positions right now.")
else:
    positions_df = pd.DataFrame(positions)
    positions_df["agent"] = positions_df["agent_id"].map(agent_map)
    positions_df = positions_df[[
        "agent", "symbol", "side", "size_pct", "entry_price", "opened_at", "rationale"
    ]]
    st.dataframe(positions_df, use_container_width=True)


st.markdown("### Decision Feed")
if not recent_decisions:
    st.info("No decisions logged yet.")
else:
    decisions_df = pd.DataFrame(recent_decisions)
    decisions_df["agent"] = decisions_df["agents"].apply(
        lambda x: x.get("name") if isinstance(x, dict) else "Unknown"
    )
    decisions_df = decisions_df[[
        "timestamp", "agent", "symbol", "proposed_action", "blocked_reason",
        "confidence", "interpretation"
    ]]
    st.dataframe(decisions_df, use_container_width=True)
