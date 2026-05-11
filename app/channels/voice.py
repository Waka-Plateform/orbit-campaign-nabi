from fastapi import APIRouter
from app.integrations import compeak
from app.storage.cosmos import set_channel_config

router = APIRouter(prefix="/api/channels/voice")

@router.get("/compeak/accounts")
async def compeak_accounts(): return {"items": await compeak.list_accounts()}

@router.get("/compeak/{account}/numbers")
async def compeak_numbers(account: str): return {"items": await compeak.list_numbers(account)}

@router.get("/compeak/{account}/trunks")
async def compeak_trunks(account: str): return {"items": await compeak.list_trunks(account)}

@router.post("/compeak/numbers/purchase")
async def purchase_number(payload: dict): return await compeak.purchase_number(payload)

@router.post("/compeak/trunk/provision")
async def provision_trunk(payload: dict): return await compeak.provision_trunk(payload)

@router.post("/select")
async def select(payload: dict): return await set_channel_config("voice", payload)
