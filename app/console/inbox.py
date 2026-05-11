from fastapi import APIRouter, HTTPException
from app.integrations.acs_email import send_email
from app.integrations.acs_sms import send_sms
from app.integrations.graph_mailbox import list_messages
from app.storage.tables import log_event, query_events

router = APIRouter(prefix="/api/console")


@router.get("/inbox/{channel}")
async def inbox(channel: str):
    if channel == "email":
        return {"items": await list_messages()}
    event_type = {"sms": "sms_in", "whatsapp": "whatsapp_in", "voice": "voice_call_completed"}.get(channel)
    if not event_type:
        raise HTTPException(status_code=404, detail="Unknown channel")
    return {"items": await query_events(event_type=event_type, limit=200)}


@router.post("/inbox/{msg_id}/reply")
async def reply(msg_id: str, payload: dict):
    channel = payload.get("channel", "email")
    if channel == "email":
        result = await send_email(payload["to"], payload.get("subject", "Re: votre demande"), payload["body"], payload.get("text", ""))
        await log_event("email_reply_sent", contact_id=payload.get("contact_id", ""), step_id="inbox", payload={"msg_id": msg_id, "provider_message_id": result.get("provider_message_id")})
        return {"ok": True, **result}
    if channel == "sms":
        result = await send_sms(payload["to"], payload["body"])
        await log_event("sms_reply_sent", contact_id=payload.get("contact_id", ""), step_id="inbox", payload={"msg_id": msg_id, "provider_message_id": result.get("provider_message_id")})
        return {"ok": True, **result}
    raise HTTPException(status_code=400, detail="Reply not supported for this channel")
