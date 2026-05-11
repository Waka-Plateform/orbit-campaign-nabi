from __future__ import annotations

import httpx
from app.config import get_secret, get_settings


async def generate_email(prompt: str, recipient: dict, override: str | None = None) -> dict:
    token = await get_secret("orbit-brain-api-key")
    payload = {
        "model": "gpt-5.5",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate one campaign email for this recipient. Return JSON with subject and html_body."},
        ],
        "recipient": recipient,
    }
    if override:
        payload["override"] = override
    async with httpx.AsyncClient(timeout=45) as client:
        res = await client.post(f"{get_settings().orbit_brain_url.rstrip('/')}/v1/campaigns/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
        res.raise_for_status()
        data = res.json()
    if "subject" in data and "html_body" in data:
        return data
    return {"subject": data.get("title", "Discutons de votre demande de devis"), "html_body": data.get("content", "")}
