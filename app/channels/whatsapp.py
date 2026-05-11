from fastapi import APIRouter
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.resource.subscriptions.aio import SubscriptionClient
from azure.mgmt.resource.resources.aio import ResourceManagementClient
from azure.mgmt.communication.aio import CommunicationServiceManagementClient
from app.storage.cosmos import set_channel_config, get_channel_config

router = APIRouter(prefix="/api/channels/whatsapp")

async def _credential(): return DefaultAzureCredential()

@router.get("/subscriptions")
async def subscriptions():
    c = await _credential(); client = SubscriptionClient(c)
    items = [s.as_dict() async for s in client.subscriptions.list()]
    await client.close(); await c.close(); return {"items": items}

@router.get("/{sub}/resource-groups")
async def resource_groups(sub: str):
    c = await _credential(); client = ResourceManagementClient(c, sub)
    items = [rg.as_dict() async for rg in client.resource_groups.list()]
    await client.close(); await c.close(); return {"items": items}

@router.get("/{sub}/{rg}/messages-services")
async def messages_services(sub: str, rg: str):
    c = await _credential(); client = CommunicationServiceManagementClient(c, sub)
    items = [r.as_dict() async for r in client.communication_services.list_by_resource_group(rg)]
    await client.close(); await c.close(); return {"items": items}

@router.get("/{svc}/channels")
async def channels(svc: str):
    config = await get_channel_config("whatsapp"); sub = config.get("whatsapp_subscription_id"); rg = config.get("whatsapp_resource_group")
    c = await _credential(); client = CommunicationServiceManagementClient(c, sub)
    items = [ch.as_dict() async for ch in client.communication_services.list_keys(rg, svc)]
    await client.close(); await c.close(); return {"items": items}

@router.post("/{svc}/channels/register")
async def register_channel(svc: str, payload: dict):
    c = await _credential(); client = CommunicationServiceManagementClient(c, payload["whatsapp_subscription_id"])
    poller = await client.communication_services.begin_create_or_update(payload["whatsapp_resource_group"], svc, payload.get("resource", {}))
    result = await poller.result(); await client.close(); await c.close(); return result.as_dict()

@router.post("/select")
async def select(payload: dict):
    return await set_channel_config("whatsapp", payload)
