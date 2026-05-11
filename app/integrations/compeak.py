from __future__ import annotations

import httpx
from app.config import get_secret
from app.storage.cosmos import get_channel_config


async def _client() -> httpx.AsyncClient:
    config = await get_channel_config("voice")
    token = await get_secret(config.get("voice_kv_credentials_ref", "compeak-api-token"))
    return httpx.AsyncClient(base_url=config.get("compeak_base_url", "https://api.compeak.com"), headers={"Authorization": f"Bearer {token}"}, timeout=30)


async def list_accounts() -> list[dict]:
    async with await _client() as client:
        r = await client.get("/v1/accounts"); r.raise_for_status(); return r.json().get("items", r.json())


async def list_numbers(account: str) -> list[dict]:
    async with await _client() as client:
        r = await client.get(f"/v1/accounts/{account}/numbers"); r.raise_for_status(); return r.json().get("items", r.json())


async def list_trunks(account: str) -> list[dict]:
    async with await _client() as client:
        r = await client.get(f"/v1/accounts/{account}/trunks"); r.raise_for_status(); return r.json().get("items", r.json())


async def purchase_number(payload: dict) -> dict:
    async with await _client() as client:
        r = await client.post("/v1/numbers/purchase", json=payload); r.raise_for_status(); return r.json()


async def provision_trunk(payload: dict) -> dict:
    async with await _client() as client:
        r = await client.post("/v1/trunks", json=payload); r.raise_for_status(); return r.json()


async def start_call(payload: dict) -> dict:
    async with await _client() as client:
        r = await client.post("/v1/calls", json=payload); r.raise_for_status(); return r.json()
