from fastapi import APIRouter, Request
from app.storage.tables import log_event

router = APIRouter(prefix="/webhooks")

@router.post("/email/delivery")
async def email_delivery(request: Request):
    body = await request.json()
    items = body if isinstance(body, list) else [body]
    logged = []
    for item in items:
        event_type = item.get("eventType", "email_event")
        mapped = "email_delivered" if "DeliveryReportReceived" in event_type else "email_failed" if "failed" in str(item).lower() else "email_bounced" if "bounce" in str(item).lower() else "email_event"
        data = item.get("data", item)
        logged.append(await log_event(mapped, contact_id=data.get("recipient", ""), step_id=data.get("stepId", ""), payload=data))
    return {"ok": True, "logged": len(logged)}
