import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.settings.config import settings
from app.api.v1.payments import router as payments_router
from app.db.session import async_session_factory
from app.infrastructure.broker import broker
from app.workers.outbox.outbox_worker import run_outbox_poller


logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    poller_task = asyncio.create_task(run_outbox_poller(async_session_factory))
    yield
    poller_task.cancel()
    await asyncio.gather(poller_task, return_exceptions=True)
    await broker.close()


app = FastAPI(
    title=settings.service_title,
    lifespan=lifespan,
    debug=settings.is_dev,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)
app.include_router(payments_router)
