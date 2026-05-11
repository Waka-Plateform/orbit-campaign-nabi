import asyncio
from app.integrations.graph_mailbox import list_messages
from app.storage.tables import log_event


async def pump_mailbox_forever():
    seen: set[str] = set()
    while True:
        try:
            for msg in await list_messages(top=25):
                msg_id = msg.get("id")
                if msg_id and msg_id not in seen:
                    seen.add(msg_id)
                    await log_event("inbox.email.new", contact_id=msg.get("from", {}).get("emailAddress", {}).get("address", ""), step_id="inbox", payload=msg)
        except Exception as exc:
            await log_event("pump.error", step_id="inbox", payload={"error": str(exc)})
        await asyncio.sleep(60)
