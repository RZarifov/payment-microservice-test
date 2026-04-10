import asyncio
import logging

from faststream import FastStream

from app.settings.config import settings
from app.db.session import async_session_factory
from app.infrastructure.broker import broker
from app.workers.consumer.handler import make_subscriber


logging.basicConfig(level=settings.log_level)


make_subscriber(async_session_factory)
worker = FastStream(broker)

asyncio.run(worker.run())
