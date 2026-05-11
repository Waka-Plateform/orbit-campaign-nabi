from fastapi import APIRouter
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.resource.subscriptions.aio import SubscriptionClient
from azure.mgmt.resource.resources.aio import ResourceManagementClient
from azure.mgmt.communication.aio import CommunicationServiceManagementClient
from app.config import get_settings
from app.storage.cosmos import set_channel_config

router = APIRouter(prefix="/api/channels/email")

async def _cred():
    return DefaultAzureCredential()

@router.get("/subscriptions")
async def subscriptions():
    credential = await _cred(); client = SubscriptionClient(credential)
    items = [s.as_dict() async for s in client.subscriptions.list()]
    await client.close(); await credential.close(); return {"items": items}

@router.get("/{sub}/resource-groups")
async def resource_groups(sub: str):
    credential = await _cred(); client = ResourceManagementClient(credential, sub)
    items = [rg.as_dict() async for rg in client.resource_groups.list()]
    await client.close(); await credential.close(); return {"items": items}

@router.get("/{sub}/{rg}/email-services")
async def email_services(sub: str, rg: str):
    credential = await _cred(); client = CommunicationServiceManagementClient(credential, sub)
    resources = [r.as_dict() async for r in client.communication_services.list_by_resource_group(rg)]
    await client.close(); await credential.close(); return {"items": resources}

@router.get("/{svc}/domains")
async def domains(svc: str):
    credential = await _cred(); client = CommunicationServiceManagementClient(credential, get_settings().azure_subscription_id)
    rg = get_settings().azure_resource_group
    items = [d.as_dict() async for d in client.domains.list_by_email_service_resource(rg, svc)]
    await client.close(); await credential.close(); return {"items": items}

@router.get("/{svc}/{domain}/senders")
async def senders(svc: str, domain: str):
    credential = await _cred(); client = CommunicationServiceManagementClient(credential, get_settings().azure_subscription_id)
    rg = get_settings().azure_resource_group
    items = [s.as_dict() async for s in client.sender_usernames.list_by_domains(rg, svc, domain)]
    await client.close(); await credential.close(); return {"items": items}

@router.post("/select")
async def select(payload: dict):
    return await set_channel_config("email", payload)

@router.post("/{svc}/domains/create")
async def create_domain(svc: str, payload: dict):
    credential = await _cred(); client = CommunicationServiceManagementClient(credential, payload.get("email_subscription_id", get_settings().azure_subscription_id))
    rg = payload.get("email_resource_group", get_settings().azure_resource_group)
    poller = await client.domains.begin_create_or_update(rg, svc, payload["domain_name"], payload.get("domain", {"location": "global", "domainManagement": payload.get("domain_management", "AzureManaged")}))
    result = await poller.result(); await client.close(); await credential.close(); return result.as_dict()

@router.post("/{svc}/{domain}/senders/create")
async def create_sender(svc: str, domain: str, payload: dict):
    credential = await _cred(); client = CommunicationServiceManagementClient(credential, payload.get("email_subscription_id", get_settings().azure_subscription_id))
    rg = payload.get("email_resource_group", get_settings().azure_resource_group)
    poller = await client.sender_usernames.begin_create_or_update(rg, svc, domain, payload["sender_username"], payload.get("sender", {"displayName": payload.get("display_name", payload["sender_username"])}))
    result = await poller.result(); await client.close(); await credential.close(); return result.as_dict()
