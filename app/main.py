"""
FastAPI Entry Point for COREXIA Agents

This provides:
- Health check endpoint
- Manual trigger for agent runs
- Status/monitoring endpoints

The CORE logic runs in worker.py via cron.
This is optional infrastructure.
"""
from datetime import datetime

from fastapi import FastAPI, HTTPException

from app.worker import run_daily
from app.supabase_client import supabase, init_agents
from app.execution.risk import check_account_health
from app.config import CAPITAL_START

app = FastAPI(
    title="COREXIA Agents",
    description="Autonomous trading agents powered by COREXIA Market Intelligence",
    version="0.1.0"
)


@app.on_event("startup")
async def startup():
    """Initialize agents in Supabase on startup"""
    try:
        init_agents()
        print("Agents initialized in Supabase")
    except Exception as e:
        print(f"Warning: Agent init failed: {e}")


@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "service": "COREXIA Agents",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/run")
def trigger_run():
    """
    Manually trigger agent run.

    Use this for testing or manual execution.
    In production, this runs via cron.
    """
    try:
        run_daily()
        return {"status": "success", "message": "Agent cycle completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
def get_status():
    """
    Get agent status summary.

    Returns equity, drawdown, and positions for all agents.
    """
    try:
        from app.supabase_client import get_agent_id

        agents = []
        for agent_name in ["Steward", "Operator", "Hunter"]:
            try:
                agent_id = get_agent_id(agent_name)
                health = check_account_health(agent_id, CAPITAL_START)

                positions = supabase.table("agent_positions")\
                    .select("*")\
                    .eq("agent_id", agent_id)\
                    .is_("closed_at", "null")\
                    .execute()

                agents.append({
                    "name": agent_name,
                    "equity": health["current_equity"],
                    "drawdown": health["drawdown"],
                    "status": health["status"],
                    "open_positions": len(positions.data)
                })
            except Exception as e:
                agents.append({
                    "name": agent_name,
                    "error": str(e)
                })

        return {
            "timestamp": datetime.now().isoformat(),
            "agents": agents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisions/recent")
def get_recent_decisions(limit: int = 20):
    """Get recent agent decisions"""
    try:
        result = supabase.table("agent_decisions")\
            .select("*, agents(name)")\
            .order("timestamp", desc=True)\
            .limit(limit)\
            .execute()

        return {
            "decisions": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
