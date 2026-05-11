from __future__ import annotations

import importlib
from datetime import datetime, timezone
from app.actions import ACTION_MODULES
from app.orchestrator.schedule import is_paused_or_outside_global_window, is_in_allowed_window, next_allowed_time, parse_iso_duration
from app.orchestrator.state import get_contact_state, initialize_contact_state, update_contact_state
from app.storage.cosmos import get_campaign
from app.storage.tables import iter_active_prospects, query_events, log_event


FLOW_NEXT = {"A": "W1", "W1": "C1", "B": "END_NO"}
END_NODES = {"END_YES", "END_NO"}


def _contact_id(recipient: dict) -> str:
    return str(recipient.get("RowKey") or recipient.get("contact_id") or recipient.get("Email Address") or "")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def _agent_clicked(contact_id: str) -> bool:
    events = await query_events(contact_id=contact_id, event_type="email_click", limit=1000)
    return any("agent" in str(e.get("payload", "")) or e.get("step_id") in ("A", "B") for e in events)


async def _run_action(node_id: str, recipient: dict, schedule: dict) -> dict:
    module = importlib.import_module(ACTION_MODULES[node_id])
    return await module.run(recipient, {"step_id": node_id, "schedule": schedule})


async def tick(limit: int = 100) -> dict:
    campaign = await get_campaign()
    schedule = campaign.get("schedule", {})
    now = datetime.now(timezone.utc)
    blocked, reason = is_paused_or_outside_global_window(schedule, now)
    if blocked:
        return {"ok": True, "status": reason, "processed": 0}
    processed = 0
    results = []
    async for recipient in iter_active_prospects():
        if processed >= limit:
            break
        contact_id = _contact_id(recipient)
        state = await get_contact_state(contact_id) or await initialize_contact_state(contact_id)
        if state.get("status") in ("finished", "stopped"):
            continue
        planned_at = _parse(state.get("planned_at")) if state.get("planned_at") else now
        if planned_at > now:
            continue
        node = state.get("node_id", "A")
        if node in END_NODES:
            await update_contact_state(contact_id, node, status="finished", last_event=state.get("last_event"))
            continue
        if node in ACTION_MODULES:
            if not is_in_allowed_window(schedule, now):
                await update_contact_state(contact_id, node, planned_at=next_allowed_time(schedule, now).isoformat(), last_event=state.get("last_event"))
                continue
            result = await _run_action(node, recipient, schedule)
            if result.get("status") == "deferred":
                await update_contact_state(contact_id, node, planned_at=result.get("resume_at"), last_event=result)
                continue
            await update_contact_state(contact_id, FLOW_NEXT[node], planned_at=now.isoformat(), last_event=result)
            await log_event("step.completed", contact_id=contact_id, step_id=node, payload=result)
            results.append(result)
            processed += 1
        elif node == "W1":
            wait_until = now + parse_iso_duration("P5D")
            await update_contact_state(contact_id, "C1", planned_at=wait_until.isoformat(), last_event=state.get("last_event"))
        elif node == "C1":
            if await _agent_clicked(contact_id):
                await update_contact_state(contact_id, "END_YES", status="finished", planned_at=now.isoformat(), last_event={"condition": "yes"})
            else:
                await update_contact_state(contact_id, "B", planned_at=now.isoformat(), last_event={"condition": "no"})
    return {"ok": True, "status": "running", "processed": processed, "results": results}
