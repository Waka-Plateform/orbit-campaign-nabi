from fastapi import APIRouter, Request
from app.storage.tables import log_event

router = APIRouter(prefix="/webhooks")

@router.post("/sms/event")
async def sms_event(request: Request):
    body = await request.json(); items = body if isinstance(body, list) else [body]
    for item in items:
        data = item.get("data", item); raw = str(item).lower()
        typ = "sms_in" if "received" in raw or "incoming" in raw else "sms_failed" if "fail" in raw else "sms_delivered"
        await log_event(typ, contact_id=data.get("from", data.get("to", "")), step_id=data.get("stepId", ""), payload=data)
    return {"ok": True, "logged": len(items)}
