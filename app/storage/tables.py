from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.data.tables.aio import TableServiceClient
from azure.identity.aio import DefaultAzureCredential
from app.config import get_settings


_credential: DefaultAzureCredential | None = None
_service: TableServiceClient | None = None


async def _table_service() -> TableServiceClient:
    global _credential, _service
    if _service is None:
        _credential = DefaultAzureCredential()
        _service = TableServiceClient(endpoint=get_settings().storage_table_endpoint, credential=_credential)
    return _service


async def ensure_tables() -> None:
    svc = await _table_service()
    for name in ("prospects", "events"):
        try:
            await svc.create_table(name)
        except ResourceExistsError:
            pass


async def list_prospects(page: int = 1, page_size: int = 100, audience: str | None = None, q: str | None = None) -> dict:
    svc = await _table_service()
    table = svc.get_table_client("prospects")
    settings = get_settings()
    filters = [f"PartitionKey eq '{settings.campaign_id}'"]
    if audience:
        filters.append(f"audience eq '{audience}'")
    query_filter = " and ".join(filters)
    rows = []
    async for entity in table.query_entities(query_filter=query_filter):
        item = dict(entity)
        hay = json.dumps(item, ensure_ascii=False).lower()
        if q and q.lower() not in hay:
            continue
        rows.append(item)
    start = max(page - 1, 0) * page_size
    return {"items": rows[start:start + page_size], "page": page, "page_size": page_size, "total": len(rows)}


async def get_prospect(contact_id: str) -> dict | None:
    table = (await _table_service()).get_table_client("prospects")
    try:
        return dict(await table.get_entity(partition_key=get_settings().campaign_id, row_key=contact_id))
    except ResourceNotFoundError:
        return None


async def iter_active_prospects() -> AsyncIterator[dict]:
    table = (await _table_service()).get_table_client("prospects")
    async for entity in table.query_entities(query_filter=f"PartitionKey eq '{get_settings().campaign_id}'"):
        item = dict(entity)
        if str(item.get("optout", "false")).lower() != "true":
            yield item


async def mark_optout(contact_id: str) -> None:
    table = (await _table_service()).get_table_client("prospects")
    entity = await table.get_entity(partition_key=get_settings().campaign_id, row_key=contact_id)
    entity["optout"] = True
    entity["optout_at"] = datetime.now(timezone.utc).isoformat()
    await table.update_entity(entity=entity, mode="Merge")


async def log_event(event_type: str, contact_id: str | None = None, step_id: str | None = None, payload: dict[str, Any] | None = None) -> dict:
    table = (await _table_service()).get_table_client("events")
    now = datetime.now(timezone.utc)
    event_id = str(uuid.uuid4())
    entity = {
        "PartitionKey": get_settings().campaign_id,
        "RowKey": f"{now.strftime('%Y%m%d%H%M%S%f')}_{event_id}",
        "event_id": event_id,
        "type": event_type,
        "contact_id": contact_id or "",
        "step_id": step_id or "",
        "ts": now.isoformat(),
        "payload": json.dumps(payload or {}, ensure_ascii=False),
    }
    await table.create_entity(entity=entity)
    return entity


async def query_events(contact_id: str | None = None, step_id: str | None = None, event_type: str | None = None, limit: int = 500) -> list[dict]:
    table = (await _table_service()).get_table_client("events")
    filters = [f"PartitionKey eq '{get_settings().campaign_id}'"]
    if contact_id:
        filters.append(f"contact_id eq '{contact_id}'")
    if step_id:
        filters.append(f"step_id eq '{step_id}'")
    if event_type:
        filters.append(f"type eq '{event_type}'")
    rows = []
    async for e in table.query_entities(query_filter=" and ".join(filters)):
        rows.append(dict(e))
        if len(rows) >= limit:
            break
    return sorted(rows, key=lambda x: x.get("RowKey", ""), reverse=True)


async def count_events_since(event_type: str, since_iso: str, step_id: str | None = None) -> int:
    rows = await query_events(step_id=step_id, event_type=event_type, limit=10000)
    return sum(1 for r in rows if r.get("ts", "") >= since_iso)
