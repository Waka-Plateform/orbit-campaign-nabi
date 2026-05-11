from __future__ import annotations

import base64
import hmac
import hashlib
from urllib.parse import quote
from app.config import get_secret, get_settings
from app.orchestrator.schedule import is_paused_or_outside_global_window, is_in_allowed_window, next_allowed_time


async def assert_schedule_allowed(ctx: dict) -> tuple[bool, dict | None]:
    schedule = ctx.get("schedule", {})
    blocked, reason = is_paused_or_outside_global_window(schedule)
    if blocked or not is_in_allowed_window(schedule):
        return False, {"ok": False, "status": "deferred", "reason": reason if blocked else "outside_allowed_window", "resume_at": next_allowed_time(schedule).isoformat()}
    return True, None


def interpolate(template: str, recipient: dict, extra: dict | None = None) -> str:
    values = {**recipient, **(extra or {})}
    out = template
    for k, v in values.items():
        out = out.replace("{{ " + k + " }}", str(v or "")).replace("{{" + k + "}}", str(v or ""))
    return out


async def unsubscribe_token(contact_id: str) -> str:
    secret = await get_secret("unsubscribe-secret")
    return hmac.new(secret.encode(), contact_id.encode(), hashlib.sha256).hexdigest()


async def tracking_context(recipient: dict, step_id: str) -> dict:
    settings = get_settings()
    contact_id = str(recipient.get("RowKey") or recipient.get("contact_id") or recipient.get("Email Address") or "")
    token = await unsubscribe_token(contact_id)
    agent_url = f"https://app.wakaorbit.com/agents/{settings.agent_text_id}?campaign_id={settings.campaign_id}&contact_id={quote(contact_id)}"
    encoded = base64.urlsafe_b64encode(agent_url.encode()).decode()
    click_url = f"{settings.public_base_url}/track/click/{step_id}?u={encoded}&contact_id={quote(contact_id)}&agent=1"
    return {
        "contact_id": contact_id,
        "agent_url": agent_url,
        "tracking_open_url": f"{settings.public_base_url}/track/open/{step_id}?contact_id={quote(contact_id)}",
        "tracking_click_url": click_url,
        "short_url": click_url,
        "unsubscribe_url": f"{settings.public_base_url}/unsubscribe/{quote(contact_id)}?t={token}",
        "stop_number": "STOP",
    }


def inject_email_tracking(html: str, tracking: dict) -> str:
    out = html.replace("{{agent_link}}", tracking["tracking_click_url"]).replace("{{ agent_link }}", tracking["tracking_click_url"])
    out = out.replace("{{unsubscribe_url}}", tracking["unsubscribe_url"]).replace("{{ unsubscribe_url }}", tracking["unsubscribe_url"])
    pixel = f'<img src="{tracking["tracking_open_url"]}" width="1" height="1" alt="" style="display:none" />'
    if "</body>" in out:
        return out.replace("</body>", pixel + "</body>")
    return out + pixel
