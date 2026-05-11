from fastapi import APIRouter
from app.actions.A_email import run as run_a
from app.actions.B_sms import run as run_b
from app.storage.cosmos import get_campaign

router = APIRouter(prefix="/actions")

@router.post("/A/run")
async def action_a(payload: dict):
    campaign = await get_campaign()
    return await run_a(payload.get("recipient", {}), {"step_id": "A", "schedule": campaign.get("schedule", {}), **payload.get("ctx", {})})

@router.post("/B/run")
async def action_b(payload: dict):
    campaign = await get_campaign()
    return await run_b(payload.get("recipient", {}), {"step_id": "B", "schedule": campaign.get("schedule", {}), **payload.get("ctx", {})})
