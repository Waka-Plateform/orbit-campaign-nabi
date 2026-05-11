from collections import Counter
from fastapi import APIRouter
from app.storage.tables import query_events

router = APIRouter(prefix="/api/console")


@router.get("/dashboard")
async def dashboard(metric: str | None = None, period: str | None = None):
    events = await query_events(limit=10000)
    counts = Counter(e.get("type") for e in events)
    sent = counts.get("email_sent", 0) + counts.get("sms_sent", 0)
    clicks = counts.get("email_click", 0) + counts.get("sms_click", 0) + counts.get("agent_link_clicked", 0)
    return {"period": period or "all", "metric": metric or "summary", "counts": counts, "kpis": {"sent": sent, "clicks": clicks, "click_rate_agent_link": (clicks / sent if sent else 0), "agent_conversation_started_count": counts.get("agent_session_started", 0), "qualified_quote_request_count": counts.get("qualified_quote_request", 0)}, "recent_events": events[:100]}
