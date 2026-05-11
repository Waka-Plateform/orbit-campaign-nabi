from fastapi import APIRouter
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.resource.subscriptions.aio import SubscriptionClient
from azure.mgmt.resource.resources.aio import ResourceManagementClient
from azure.mgmt.communication.aio import CommunicationServiceManagementClient
from app.storage.cosmos import set_channel_config, get_channel_config

router = APIRouter(prefix="/api/channels/sms")

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

@router.get("/{sub}/{rg}/communication-services")
async def communication_services(sub: str, rg: str):
    c = await _credential(); client = CommunicationServiceManagementClient(c, sub)
    items = [r.as_dict() async for r in client.communication_services.list_by_resource_group(rg)]
    await client.close(); await c.close(); return {"items": items}

@router.get("/{svc}/phone-numbers")
async def phone_numbers(svc: str):
    config = await get_channel_config("sms"); sub = config.get("sms_subscription_id"); rg = config.get("sms_resource_group")
    c = await _credential(); client = CommunicationServiceManagementClient(c, sub)
    items = [n.as_dict() async for n in client.phone_numbers.list_by_communication_service(rg, svc)]
    await client.close(); await c.close(); return {"items": items}

@router.post("/{svc}/phone-numbers/purchase")
async def purchase_phone_number(svc: str, payload: dict):
    c = await _credential(); client = CommunicationServiceManagementClient(c, payload["sms_subscription_id"])
    poller = await client.phone_numbers.begin_create_or_update(payload["sms_resource_group"], svc, payload["phone_number"], payload)
    result = await poller.result(); await client.close(); await c.close(); return result.as_dict()

@router.post("/select")
async def select(payload: dict):
    return await set_channel_config("sms", payload)
