from __future__ import annotations

from azure.communication.email.aio import EmailClient
from azure.identity.aio import DefaultAzureCredential
from app.storage.cosmos import get_channel_config
from app.config import get_settings


async def send_email(to_address: str, subject: str, html_body: str, text_body: str = "") -> dict:
    config = await get_channel_config("email")
    endpoint = config.get("email_communication_service_endpoint") or config.get("endpoint")
    if not endpoint:
        service_id = config.get("email_communication_service_id", "")
        name = service_id.rstrip("/").split("/")[-1]
        endpoint = f"https://{name}.communication.azure.com"
    sender = f"{config.get('email_sender_username')}@{config.get('email_domain')}"
    credential = DefaultAzureCredential()
    client = EmailClient(endpoint=endpoint, credential=credential)
    message = {
        "senderAddress": sender,
        "recipients": {"to": [{"address": to_address}]},
        "content": {"subject": subject, "html": html_body, "plainText": text_body or subject},
    }
    if config.get("email_reply_to"):
        message["replyTo"] = [{"address": config["email_reply_to"]}]
    poller = await client.begin_send(message)
    result = await poller.result()
    await client.close()
    await credential.close()
    return {"provider_message_id": getattr(result, "message_id", None) or result.get("id", ""), "raw": dict(result) if isinstance(result, dict) else str(result)}
