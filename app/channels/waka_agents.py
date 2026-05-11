from fastapi import APIRouter
from app.storage.cosmos import list_waka_agents, set_channel_config

router = APIRouter(prefix="/api/channels")

@router.get("/text/agents")
async def text_agents(): return {"items": await list_waka_agents("text")}

@router.get("/voice/agents")
async def voice_agents(): return {"items": await list_waka_agents("voice")}

@router.get("/avatar/agents")
async def avatar_agents(): return {"items": await list_waka_agents("avatar")}

@router.post("/text/select")
async def select_text(payload: dict): return await set_channel_config("agents_waka", {"agent_text_id": payload["agent_text_id"]})

@router.post("/voice/select")
async def select_voice(payload: dict): return await set_channel_config("agents_waka", {"agent_voice_id": payload["agent_voice_id"]})

@router.post("/avatar/select")
async def select_avatar(payload: dict): return await set_channel_config("agents_waka", {"agent_avatar_id": payload["agent_avatar_id"]})
