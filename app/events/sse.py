import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.storage.tables import query_events

router = APIRouter()

async def _stream():
    seen = set()
    while True:
        events = await query_events(limit=50)
        for event in reversed(events):
            key = event.get("RowKey")
            if key not in seen:
                seen.add(key)
                yield f"event: {event.get('type', 'message')}\ndata: {json.dumps(event, default=str)}\n\n"
        await asyncio.sleep(5)

@router.get("/events")
async def events():
    return StreamingResponse(_stream(), media_type="text/event-stream")
