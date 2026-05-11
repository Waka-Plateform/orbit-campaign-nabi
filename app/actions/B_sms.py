from __future__ import annotations

from app.actions.common import assert_schedule_allowed, interpolate, tracking_context
from app.integrations.acs_sms import send_sms
from app.storage.blob import read_blob_text
from app.storage.cosmos import get_campaign
from app.storage.tables import log_event


def _phone_of(recipient: dict) -> str:
    return recipient.get("Phone Number") or recipient.get("phone") or recipient.get("Mobile") or ""


async def run(recipient: dict, ctx: dict) -> dict:
    allowed, deferred = await assert_schedule_allowed(ctx)
    if not allowed:
        return deferred
    step_id = ctx.get("step_id", "B")
    campaign = await get_campaign()
    artifact = next(a for a in campaign.get("artifacts", []) if a.get("artifact_id") == "art_sms_B")
    template = await read_blob_text(artifact["blob_path"])
    tracking = await tracking_context(recipient, step_id)
    body = interpolate(template, recipient, tracking)
    result = await send_sms(_phone_of(recipient), body)
    event = await log_event("sms_sent", contact_id=tracking["contact_id"], step_id=step_id, payload={"provider_message_id": result.get("provider_message_id"), "body_len": len(body)})
    return {"ok": True, "step_id": step_id, "recipient_id": tracking["contact_id"], "provider_message_id": result.get("provider_message_id"), "status": "sent", "event_id": event["event_id"]}
