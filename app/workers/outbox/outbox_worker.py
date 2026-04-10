import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models.payment import Outbox
from app.infrastructure.broker import broker
from app.settings.config import settings


logger = logging.getLogger(__name__)


async def _poll_once(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session:
        result = await session.execute(
            select(Outbox)
            .where(Outbox.published_at.is_(None))
            .with_for_update(skip_locked=True)
        )
        entries = result.scalars().all()

        for entry in entries:
            await broker.publish(
                {"payment_id": str(entry.payment_id)},
                queue="payments.new",
            )
            entry.published_at = datetime.now(timezone.utc)

        await session.commit()


async def run_outbox_poller(factory: async_sessionmaker[AsyncSession]) -> None:
    while True:
        try:
            await _poll_once(factory)
        except Exception:
            logger.exception("outbox poll failed")
        await asyncio.sleep(settings.outbox_poll_interval)
