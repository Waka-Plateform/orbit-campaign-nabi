import base64
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.storage.tables import log_event

router = APIRouter()


@router.get("/track/click/{step_id}")
async def track_click(step_id: str, request: Request, u: str, contact_id: str = "", agent: str = "0"):
    target = base64.urlsafe_b64decode(u.encode()).decode()
    await log_event("email_click" if step_id == "A" else "sms_click", contact_id=contact_id, step_id=step_id, payload={"url": target, "agent": agent == "1", "ip": request.client.host if request.client else "", "user_agent": request.headers.get("user-agent", "")})
    if agent == "1":
        await log_event("agent_link_clicked", contact_id=contact_id, step_id=step_id, payload={"url": target})
    return RedirectResponse(target, status_code=302)
