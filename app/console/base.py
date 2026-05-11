from fastapi import APIRouter, Query
from app.storage.tables import list_prospects

router = APIRouter(prefix="/api/console")


@router.get("/base")
async def console_base(page: int = 1, audience: str | None = None, q: str | None = None, page_size: int = Query(100, le=500)):
    return await list_prospects(page=page, page_size=page_size, audience=audience, q=q)
