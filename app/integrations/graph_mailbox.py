from __future__ import annotations

import httpx
from azure.identity.aio import DefaultAzureCredential
from app.config import get_settings


async def _graph_token() -> str:
    credential = DefaultAzureCredential()
    token = await credential.get_token("https://graph.microsoft.com/.default")
    await credential.close()
    return token.token


async def list_messages(top: int = 50) -> list[dict]:
    token = await _graph_token()
    mailbox = get_settings().shared_mailbox_address
    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages?$top={top}&$orderby=receivedDateTime desc"
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        res.raise_for_status()
        return res.json().get("value", [])
