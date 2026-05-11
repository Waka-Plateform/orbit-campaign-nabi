from fastapi import APIRouter
from app.storage.cosmos import get_campaign
from app.config import get_settings

router = APIRouter(prefix="/api/console")


@router.get("/main")
async def console_main():
    campaign = await get_campaign()
    return {
        "campaign_id": get_settings().campaign_id,
        "slug": get_settings().campaign_slug,
        "name": campaign.get("name"),
        "objective": campaign.get("scope_brief", {}).get("objective"),
        "flow_graph": campaign.get("scope_brief", {}).get("flow_graph"),
        "flow_svg_url": f"/api/launch/campaigns/{get_settings().campaign_id}/flow.svg",
        "metrics": campaign.get("scope_brief", {}).get("success_metrics", []),
        "channels": campaign.get("channels", {}),
    }
