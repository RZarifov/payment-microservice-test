import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.payments import router as payments_router
from app.db.session import async_session_factory
from app.infrastructure.broker import broker
from app.workers.outbox.outbox_worker import run_outbox_poller


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    poller_task = asyncio.create_task(run_outbox_poller(async_session_factory))
    yield
    poller_task.cancel()
    await broker.close()


app = FastAPI(title="Luna Payment Service", lifespan=lifespan)
app.include_router(payments_router)
