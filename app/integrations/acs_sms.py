from __future__ import annotations

from azure.communication.sms.aio import SmsClient
from azure.identity.aio import DefaultAzureCredential
from app.storage.cosmos import get_channel_config


async def send_sms(to_number: str, body: str) -> dict:
    config = await get_channel_config("sms")
    endpoint = config.get("sms_communication_service_endpoint") or config.get("endpoint")
    if not endpoint:
        service_id = config.get("sms_communication_service_id", "")
        name = service_id.rstrip("/").split("/")[-1]
        endpoint = f"https://{name}.communication.azure.com"
    from_number = config.get("sms_phone_number")
    credential = DefaultAzureCredential()
    client = SmsClient(endpoint=endpoint, credential=credential)
    responses = await client.send(from_=from_number, to=[to_number], message=body, enable_delivery_report=True)
    await client.close()
    await credential.close()
    first = responses[0] if responses else {}
    return {"provider_message_id": getattr(first, "message_id", None) or first.get("message_id", ""), "raw": dict(first) if isinstance(first, dict) else str(first)}
