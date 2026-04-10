import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.db.models.payment import Payment, PaymentStatus
from app.infrastructure.broker import broker
from app.workers.consumer.webhook import send_webhook


logger = logging.getLogger(__name__)


async def _emulate_processing() -> bool:
    await asyncio.sleep(random.uniform(2, 5))
    return random.random() < 0.9


async def process_payment(payment_id: str, factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session:
        result = await session.execute(select(Payment).where(Payment.id == uuid.UUID(payment_id)))
        payment = result.scalar_one_or_none()

        if not payment:
            logger.error("payment %s not found", payment_id)
            return

        success = await _emulate_processing()
        payment.status = PaymentStatus.succeeded if success else PaymentStatus.failed
        payment.processed_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(payment)

        webhook_payload = {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "amount": str(payment.amount),
            "currency": payment.currency.value,
        }

        webhook_url = payment.webhook_url

    delivered = await send_webhook(webhook_url, webhook_payload)

    if not delivered:
        logger.error("webhook delivery exhausted for payment %s, publishing to DLQ", payment_id)
        await broker.publish(
            {"payment_id": payment_id, "reason": "webhook_delivery_failed"},
            queue="payments.dlq",
        )


def make_subscriber(factory: async_sessionmaker[AsyncSession]):
    @broker.subscriber("payments.new")
    async def handle_payment(data: dict) -> None:
        await process_payment(data["payment_id"], factory)

    return handle_payment
