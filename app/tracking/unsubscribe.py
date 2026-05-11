import hmac
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.actions.common import unsubscribe_token
from app.storage.tables import log_event, mark_optout

router = APIRouter()


@router.get("/unsubscribe/{contact_id}")
async def unsubscribe(contact_id: str, t: str):
    expected = await unsubscribe_token(contact_id)
    if not hmac.compare_digest(expected, t):
        raise HTTPException(status_code=403, detail="Invalid unsubscribe token")
    await mark_optout(contact_id)
    await log_event("email_unsubscribe", contact_id=contact_id, step_id="unsubscribe", payload={})
    return HTMLResponse("<html><body><h1>Désinscription confirmée</h1><p>Vous ne recevrez plus cette campagne.</p></body></html>")
