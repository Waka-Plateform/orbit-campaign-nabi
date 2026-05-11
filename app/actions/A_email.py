from __future__ import annotations

import re
from app.actions.common import assert_schedule_allowed, inject_email_tracking, tracking_context
from app.integrations.acs_email import send_email
from app.integrations.orbit_brain import generate_email
from app.storage.blob import read_blob_text
from app.storage.cosmos import get_campaign
from app.storage.tables import log_event


def _email_of(recipient: dict) -> str:
    return recipient.get("Email Address") or recipient.get("email") or recipient.get("Email") or ""


def _plain(html: str) -> str:
    return re.sub("<[^>]+>", " ", html).strip()


async def run(recipient: dict, ctx: dict) -> dict:
    allowed, deferred = await assert_schedule_allowed(ctx)
    if not allowed:
        return deferred
    step_id = ctx.get("step_id", "A")
    campaign = await get_campaign()
    artifact = next(a for a in campaign.get("artifacts", []) if a.get("artifact_id") == "art_email_A")
    prompt = await read_blob_text(artifact["blob_path"])
    tracking = await tracking_context(recipient, step_id)
    generated = await generate_email(prompt=prompt, recipient={**recipient, **tracking}, override=ctx.get("source_override"))
    subject = generated.get("subject") or "Discutons de votre demande de devis"
    html = inject_email_tracking(generated.get("html_body") or generated.get("html") or "", tracking)
    result = await send_email(_email_of(recipient), subject, html, _plain(html))
    event = await log_event("email_sent", contact_id=tracking["contact_id"], step_id=step_id, payload={"provider_message_id": result.get("provider_message_id"), "subject": subject})
    return {"ok": True, "step_id": step_id, "recipient_id": tracking["contact_id"], "provider_message_id": result.get("provider_message_id"), "status": "sent", "event_id": event["event_id"]}
