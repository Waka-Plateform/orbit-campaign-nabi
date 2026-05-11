from fastapi import APIRouter, Request, Response
from app.storage.tables import log_event

router = APIRouter()
GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


@router.get("/track/open/{step_id}")
async def track_open(step_id: str, request: Request, contact_id: str = ""):
    await log_event("email_open", contact_id=contact_id, step_id=step_id, payload={"ip": request.client.host if request.client else "", "user_agent": request.headers.get("user-agent", "")})
    return Response(content=GIF, media_type="image/gif", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
