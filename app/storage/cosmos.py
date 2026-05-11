from __future__ import annotations

from typing import Any
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from app.config import get_settings


_credential: DefaultAzureCredential | None = None
_client: CosmosClient | None = None


async def _cosmos_client() -> CosmosClient:
    global _credential, _client
    settings = get_settings()
    if _client is None:
        _credential = DefaultAzureCredential()
        _client = CosmosClient(settings.cosmos_endpoint, credential=_credential)
    return _client


async def campaign_container():
    settings = get_settings()
    client = await _cosmos_client()
    return client.get_database_client(settings.cosmos_database).get_container_client(settings.cosmos_campaigns_container)


async def get_campaign() -> dict:
    container = await campaign_container()
    return dict(await container.read_item(item=get_settings().campaign_id, partition_key=get_settings().campaign_id))


async def patch_campaign(operations: list[dict[str, Any]]) -> dict:
    container = await campaign_container()
    return dict(await container.patch_item(item=get_settings().campaign_id, partition_key=get_settings().campaign_id, patch_operations=operations))


async def merge_campaign_fields(fields: dict[str, Any]) -> dict:
    campaign = await get_campaign()
    campaign.update(fields)
    container = await campaign_container()
    return dict(await container.upsert_item(campaign))


async def get_channel_config(channel: str) -> dict:
    campaign = await get_campaign()
    return campaign.get("channels", {}).get(channel, {}).get("config", {})


async def set_channel_config(channel: str, config: dict) -> dict:
    campaign = await get_campaign()
    channels = campaign.setdefault("channels", {})
    channel_doc = channels.setdefault(channel, {"enabled": True})
    channel_doc["config"] = config
    return await merge_campaign_fields({"channels": channels})


async def get_runtime_state() -> dict:
    return (await get_campaign()).get("runtime_state", {})


async def set_contact_state(contact_id: str, state: dict) -> dict:
    campaign = await get_campaign()
    runtime = campaign.setdefault("runtime_state", {})
    runtime[contact_id] = state
    return await merge_campaign_fields({"runtime_state": runtime})


async def set_schedule(schedule: dict) -> dict:
    return await merge_campaign_fields({"schedule": schedule})


async def list_waka_agents(agent_type: str) -> list[dict]:
    settings = get_settings()
    client = await _cosmos_client()
    container = client.get_database_client(settings.conversations_database).get_container_client(settings.conversations_agents_container)
    query = "SELECT * FROM c WHERE c.type = @type OR c.agent_type = @type"
    rows = []
    async for item in container.query_items(query=query, parameters=[{"name":"@type","value":agent_type}], enable_cross_partition_query=True):
        rows.append(dict(item))
    return rows
