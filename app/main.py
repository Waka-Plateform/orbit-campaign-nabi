from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.actions.routes import router as actions_router
from app.channels import email, sms, whatsapp, voice, waka_agents
from app.console import main as console_main, base, plan, sources, dashboard, inbox
from app.events.pump import pump_mailbox_forever
from app.events.sse import router as sse_router
from app.storage.tables import ensure_tables
from app.tracking.open import router as open_router
from app.tracking.click import router as click_router
from app.tracking.unsubscribe import router as unsubscribe_router
from app.webhooks import email_delivery, sms_event, whatsapp_event, voice_event, agent_callback


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_tables()
    task = asyncio.create_task(pump_mailbox_forever())
    yield
    task.cancel()


app = FastAPI(title="Orbit Campaign nabi", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for router in [
    actions_router,
    console_main.router, base.router, plan.router, sources.router, dashboard.router, inbox.router,
    email.router, sms.router, whatsapp.router, voice.router, waka_agents.router,
    open_router, click_router, unsubscribe_router,
    email_delivery.router, sms_event.router, whatsapp_event.router, voice_event.router, agent_callback.router,
    sse_router,
]:
    app.include_router(router)


@app.get("/health")
async def health():
    return {"ok": True, "service": "orbit-campaign-nabi"}
