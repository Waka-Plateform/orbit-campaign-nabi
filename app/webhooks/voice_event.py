from fastapi import APIRouter, Request
from app.storage.tables import log_event

router = APIRouter(prefix="/webhooks")

@router.post("/voice/event")
async def voice_event(request: Request):
    data = await request.json()
    typ = "voice_transcript" if data.get("transcript") else "voice_call_completed"
    await log_event(typ, contact_id=data.get("contact_id", data.get("to", "")), step_id=data.get("step_id", "voice"), payload=data)
    return {"ok": True}
