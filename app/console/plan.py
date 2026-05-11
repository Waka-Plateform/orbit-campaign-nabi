from datetime import datetime, timezone
from fastapi import APIRouter
from app.orchestrator.runner import tick
from app.storage.cosmos import get_campaign, set_schedule

router = APIRouter(prefix="/api/console")


@router.get("/plan")
async def get_plan():
    return (await get_campaign()).get("schedule", {})


@router.post("/plan")
async def post_plan(schedule: dict):
    return await set_schedule(schedule)


@router.post("/plan/start")
async def start_plan():
    schedule = (await get_campaign()).get("schedule", {})
    schedule["paused"] = False
    schedule["start_at"] = datetime.now(timezone.utc).isoformat()
    await set_schedule(schedule)
    return {"ok": True, "schedule": schedule}


@router.post("/plan/pause")
async def pause_plan():
    schedule = (await get_campaign()).get("schedule", {})
    schedule["paused"] = True
    await set_schedule(schedule)
    return {"ok": True, "schedule": schedule}


@router.post("/plan/resume")
async def resume_plan():
    schedule = (await get_campaign()).get("schedule", {})
    schedule["paused"] = False
    await set_schedule(schedule)
    return {"ok": True, "schedule": schedule}


@router.post("/plan/stop")
async def stop_plan():
    schedule = (await get_campaign()).get("schedule", {})
    schedule["end_at"] = datetime.now(timezone.utc).isoformat()
    await set_schedule(schedule)
    return {"ok": True, "schedule": schedule}


@router.post("/plan/tick")
async def run_tick():
    return await tick()
