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
    page_title="COREXIA Console",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Sora:wght@400;600;700&display=swap');

:root {
  --bg: #f4f1eb;
  --panel: #ffffff;
  --ink: #101112;
  --muted: #5a5854;
  --line: #e0d7ca;
  --accent: #0b3d91;
  --accent-2: #b48a3a;
  --danger: #b91c1c;
  --shadow: rgba(15, 23, 42, 0.08);
}

html, body, [class*="stApp"] {
  background: var(--bg);
  color: var(--ink);
  font-family: "IBM Plex Sans", sans-serif;
}

h1, h2, h3 {
  font-family: "Sora", sans-serif;
  letter-spacing: -0.01em;
}

.block-container {
  padding-top: 1.6rem;
}

.hero {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.hero-title {
  font-size: 2.1rem;
  font-weight: 700;
}

.hero-sub {
  color: var(--muted);
  font-size: 1rem;
}

.breadcrumb {
  color: var(--muted);
  font-size: 0.85rem;
  margin: 6px 0 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 12px 26px var(--shadow);
}

.card-title {
  font-size: 0.85rem;
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
  background: rgba(11, 61, 145, 0.1);
  color: var(--accent);
  font-weight: 600;
}

.pill.warn {
  background: rgba(180, 138, 58, 0.16);
  color: var(--accent-2);
}

.pill.danger {
  background: rgba(185, 28, 28, 0.12);
  color: var(--danger);
}

.metric-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.95rem;
  margin-top: 6px;
  color: var(--muted);
}

.terminal {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.9rem;
  background: #0f141c;
  color: #e2e8f0;
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.2);
}

.terminal .muted {
  color: #94a3b8;
}

.nav-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-chip {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--panel);
  font-size: 0.85rem;
  font-weight: 600;
}

.login-card {
  max-width: 420px;
  margin: 8vh auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 28px;
  box-shadow: 0 20px 40px var(--shadow);
}

.login-card h2 {
  margin-top: 0;
}

.stButton > button {
  border-radius: 10px;
  border: 1px solid var(--line);
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


def _get_secret(key: str):
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def get_admin_credentials():
    admin_user = _get_secret("COREXIA_ADMIN_USER") or os.getenv("COREXIA_ADMIN_USER") or "admin"
    admin_password = _get_secret("COREXIA_ADMIN_PASSWORD") or os.getenv("COREXIA_ADMIN_PASSWORD")
    return admin_user, admin_password


def render_login():
    admin_user, admin_password = get_admin_credentials()
    if not admin_password:
        st.error("Admin password missing. Set COREXIA_ADMIN_PASSWORD in the environment.")
        st.stop()

    st.markdown(
        """
<div class="login-card">
  <h2>COREXIA Console</h2>
  <p>Secure administrative access required.</p>
</div>
        """,
        unsafe_allow_html=True
    )

    with st.form("login", clear_on_submit=False):
        username = st.text_input("Username", value=admin_user)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
        if submitted:
            if username == admin_user and password == admin_password:
                st.session_state["auth_ok"] = True
                st.session_state["auth_user"] = username
                st.session_state["page"] = "Home"
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()


def ensure_auth():
    if not st.session_state.get("auth_ok"):
        render_login()


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    key = anon_key or service_key
    if anon_key and not anon_key.startswith("eyJ"):
        key = service_key
    if not url or not key:
        return None, "Missing SUPABASE_URL or SUPABASE_ANON_KEY/SUPABASE_SERVICE_KEY"
    try:
        return create_client(url, key), None
    except Exception as exc:
        return None, str(exc)


@st.cache_data(ttl=60)
def fetch_agents(supabase):
    return supabase.table("agents").select("*").execute().data


@st.cache_data(ttl=60)
def fetch_latest_regime(supabase, symbol: str):
    result = supabase.table("market_regime_archive")\
        .select("*")\
        .eq("symbol", symbol)\
        .order("date", desc=True)\
        .limit(1)\
        .execute()
    return result.data[0] if result.data else None


@st.cache_data(ttl=60)
def fetch_recent_decisions(supabase, limit: int = 40):
    result = supabase.table("agent_decisions")\
        .select("*, agents(name)")\
        .order("timestamp", desc=True)\
        .limit(limit)\
        .execute()
    return result.data


@st.cache_data(ttl=60)
def fetch_open_positions(supabase):
    result = supabase.table("agent_positions")\
        .select("*")\
        .is_("closed_at", "null")\
        .order("opened_at", desc=True)\
        .execute()
    return result.data


@st.cache_data(ttl=60)
def fetch_performance(supabase):
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


def render_nav():
    pages = ["Home", "Observability", "Performance", "History", "Commentary", "System"]
    current = st.session_state.get("page", "Home")
    nav_cols = st.columns(len(pages) + 1)
    for col, page in zip(nav_cols[:-1], pages):
        if col.button(page, key=f"nav-{page}"):
            st.session_state["page"] = page
            st.rerun()
    if nav_cols[-1].button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.markdown(f"<div class='breadcrumb'>Corexia OS / Admin / {current}</div>", unsafe_allow_html=True)
    return current


def render_home(supabase):
    symbol = st.selectbox("Market Snapshot", ["SPY", "QQQ", "IWM", "DIA", "VIX"], index=0)
    market = fetch_latest_regime(supabase, symbol)
    agents = fetch_agents(supabase)
    positions = fetch_open_positions(supabase)
    recent_decisions = fetch_recent_decisions(supabase)
    perf = fetch_performance(supabase)

    st.markdown("### Terminal Overview")
    total_agents = len(agents) if agents else 0
    open_positions = len(positions)
    last_decision_time = recent_decisions[0]["timestamp"] if recent_decisions else "n/a"
    last_regime = market.get("market_state") if market else "n/a"

    st.markdown(
        f"""
<div class="terminal">
  <div>corexia@admin:~$ status</div>
  <div class="muted">timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
  <div class="muted">active agents: {total_agents}</div>
  <div class="muted">open positions: {open_positions}</div>
  <div class="muted">last decision: {last_decision_time}</div>
  <div class="muted">market regime ({symbol}): {last_regime}</div>
</div>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns(3)
    cols[0].markdown(
        "<div class='card'><div class='card-title'>System posture</div>"
        "<div class='card-value'>Operational</div>"
        "<div class='card-sub'>Supabase telemetry online</div></div>",
        unsafe_allow_html=True
    )
    cols[1].markdown(
        "<div class='card'><div class='card-title'>Cadence</div>"
        "<div class='card-value'>Key sessions</div>"
        "<div class='card-sub'>US session anchors enforced</div></div>",
        unsafe_allow_html=True
    )
    cols[2].markdown(
        "<div class='card'><div class='card-title'>Data horizon</div>"
        "<div class='card-value'>Persistent</div>"
        "<div class='card-sub'>Historical cache retained</div></div>",
        unsafe_allow_html=True
    )


def render_observability(supabase):
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

    agents = fetch_agents(supabase)
    agent_map = {agent["id"]: agent["name"] for agent in agents} if agents else {}
    market = fetch_latest_regime(supabase, symbol)

    st.markdown("### Live Market Context")
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
    positions = fetch_open_positions(supabase)
    positions_by_agent = {}
    for position in positions:
        positions_by_agent.setdefault(position["agent_id"], []).append(position)

    perf = fetch_performance(supabase)
    perf_df = pd.DataFrame(perf)
    latest_perf = {}
    if not perf_df.empty:
        perf_df["date"] = pd.to_datetime(perf_df["date"])
        latest = perf_df.sort_values("date").groupby("agent_id").tail(1)
        for _, row in latest.iterrows():
            latest_perf[row["agent_id"]] = row.to_dict()

    recent_decisions = fetch_recent_decisions(supabase)
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


def render_performance(supabase):
    perf = fetch_performance(supabase)
    perf_df = pd.DataFrame(perf)
    agents = fetch_agents(supabase)
    agent_map = {agent["id"]: agent["name"] for agent in agents} if agents else {}

    st.markdown("### Equity Curves")
    if perf_df.empty:
        st.info("No performance data yet. The worker will populate this table after runs.")
        return
    perf_df["date"] = pd.to_datetime(perf_df["date"])
    perf_df["agent"] = perf_df["agent_id"].map(agent_map)
    equity_pivot = perf_df.pivot(index="date", columns="agent", values="equity")
    st.line_chart(equity_pivot, use_container_width=True)

    st.markdown("### Performance Ledger")
    st.dataframe(perf_df.sort_values("date", ascending=False), use_container_width=True)


def render_history(supabase):
    st.markdown("### Open Positions")
    positions = fetch_open_positions(supabase)
    agents = fetch_agents(supabase)
    agent_map = {agent["id"]: agent["name"] for agent in agents} if agents else {}
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
    recent_decisions = fetch_recent_decisions(supabase)
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


def render_commentary(supabase):
    st.markdown("### Market Commentary")
    market = fetch_latest_regime(supabase, "SPY")
    if market:
        st.info(market.get("market_spine") or "No market spine recorded yet.")
    else:
        st.info("No market spine recorded yet.")

    st.markdown("### Narrative Stream")
    decisions = fetch_recent_decisions(supabase, limit=60)
    if not decisions:
        st.info("No commentary logged yet.")
        return
    commentary_df = pd.DataFrame(decisions)
    commentary_df["agent"] = commentary_df["agents"].apply(
        lambda x: x.get("name") if isinstance(x, dict) else "Unknown"
    )
    commentary_df = commentary_df[[
        "timestamp", "agent", "symbol", "interpretation", "blocked_reason"
    ]]
    st.dataframe(commentary_df, use_container_width=True)


def render_system(supabase):
    st.markdown("### System Diagnostics")
    env_ok = all([os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")])
    cols = st.columns(3)
    cols[0].markdown(
        f"<div class='card'><div class='card-title'>Environment</div>"
        f"<div class='card-value'>{'OK' if env_ok else 'Check'}</div>"
        f"<div class='card-sub'>Supabase config</div></div>",
        unsafe_allow_html=True
    )
    cols[1].markdown(
        f"<div class='card'><div class='card-title'>Cache</div>"
        f"<div class='card-value'>{os.getenv('COREXIA_CACHE_DIR', 'memory')}</div>"
        f"<div class='card-sub'>Scanner disk cache</div></div>",
        unsafe_allow_html=True
    )
    cols[2].markdown(
        f"<div class='card'><div class='card-title'>Auth</div>"
        f"<div class='card-value'>Admin</div>"
        f"<div class='card-sub'>{st.session_state.get('auth_user', 'admin')}</div></div>",
        unsafe_allow_html=True
    )

    if st.button("Clear cached data"):
        st.cache_data.clear()
        st.success("Cache cleared.")


def main():
    ensure_auth()

    if create_client is None:
        st.error("Supabase client not available. Install dependencies: pip install -r requirements.txt")
        st.stop()

    supabase, supabase_error = get_supabase_client()
    if supabase_error:
        st.error(f"Supabase not configured: {supabase_error}")
        st.stop()

    st.markdown(
        """
<div class="hero">
  <div class="hero-title">COREXIA Admin Console</div>
  <div class="hero-sub">Institutional observability, history, and commentary.</div>
</div>
        """,
        unsafe_allow_html=True
    )

    current_page = render_nav()

    if current_page == "Home":
        render_home(supabase)
    elif current_page == "Observability":
        render_observability(supabase)
    elif current_page == "Performance":
        render_performance(supabase)
    elif current_page == "History":
        render_history(supabase)
    elif current_page == "Commentary":
        render_commentary(supabase)
    elif current_page == "System":
        render_system(supabase)


if __name__ == "__main__":
    main()
