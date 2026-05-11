from fastapi import APIRouter, Request
from app.storage.tables import log_event

router = APIRouter(prefix="/webhooks")

@router.post("/whatsapp/event")
async def whatsapp_event(request: Request):
    body = await request.json(); items = body if isinstance(body, list) else [body]
    for item in items:
        data = item.get("data", item); raw = str(item).lower()
        typ = "whatsapp_in" if "incoming" in raw or "received" in raw else "whatsapp_delivered"
        await log_event(typ, contact_id=data.get("from", data.get("to", "")), step_id=data.get("stepId", ""), payload=data)
    return {"ok": True, "logged": len(items)}
