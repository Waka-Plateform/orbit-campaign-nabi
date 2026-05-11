from __future__ import annotations

from datetime import datetime, timezone
from app.storage.cosmos import get_runtime_state, set_contact_state


async def get_contact_state(contact_id: str) -> dict | None:
    return (await get_runtime_state()).get(contact_id)


async def initialize_contact_state(contact_id: str) -> dict:
    state = {"node_id": "A", "status": "active", "planned_at": datetime.now(timezone.utc).isoformat(), "last_event": None}
    await set_contact_state(contact_id, state)
    return state


async def update_contact_state(contact_id: str, node_id: str, status: str = "active", planned_at: str | None = None, last_event: dict | None = None) -> dict:
    state = {"node_id": node_id, "status": status, "planned_at": planned_at or datetime.now(timezone.utc).isoformat(), "last_event": last_event}
    await set_contact_state(contact_id, state)
    return state
