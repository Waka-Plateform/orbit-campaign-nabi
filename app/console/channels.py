from fastapi import APIRouter
from app.storage.cosmos import get_campaign

router = APIRouter(prefix="/api/console")


@router.get("/channels")
async def console_channels():
    campaign = await get_campaign()
    channels = campaign.get("channels", {})
    return {
        "channels": channels,
        "enabled": {name: bool(doc.get("enabled")) for name, doc in channels.items()},
        "configs": {name: doc.get("config", {}) for name, doc in channels.items()},
        "agents": campaign.get("agents", {}),
        "cascade": {
            "email": {
                "subscriptions": "/api/channels/email/subscriptions",
                "resource_groups": "/api/channels/email/{sub}/resource-groups",
                "services": "/api/channels/email/{sub}/{rg}/email-services",
                "domains": "/api/channels/email/{svc}/domains",
                "senders": "/api/channels/email/{svc}/{domain}/senders",
                "select": "/api/channels/email/select",
            },
            "sms": {
                "subscriptions": "/api/channels/sms/subscriptions",
                "resource_groups": "/api/channels/sms/{sub}/resource-groups",
                "services": "/api/channels/sms/{sub}/{rg}/communication-services",
                "phone_numbers": "/api/channels/sms/{svc}/phone-numbers",
                "select": "/api/channels/sms/select",
            },
            "agents_waka": {
                "text_agents": "/api/channels/text/agents",
                "voice_agents": "/api/channels/voice/agents",
                "avatar_agents": "/api/channels/avatar/agents",
                "select_text": "/api/channels/text/select",
                "select_voice": "/api/channels/voice/select",
                "select_avatar": "/api/channels/avatar/select",
            },
        },
    }
