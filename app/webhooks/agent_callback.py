from fastapi import APIRouter, Request
from app.storage.tables import log_event

router = APIRouter(prefix="/webhooks")

@router.post("/agent/{agent_id}")
async def agent_callback(agent_id: str, request: Request):
    data = await request.json()
    status = data.get("status", "event")
    typ = "agent_session_completed" if status == "completed" else "agent_session_started" if status == "started" else data.get("event_type", "agent_event")
    if data.get("qualified_quote_request"):
        await log_event("qualified_quote_request", contact_id=data.get("contact_id", ""), step_id="agent", payload={"agent_id": agent_id, **data})
    await log_event(typ, contact_id=data.get("contact_id", ""), step_id="agent", payload={"agent_id": agent_id, **data})
    return {"ok": True}
