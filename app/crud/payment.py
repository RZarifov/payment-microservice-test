import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Outbox, Payment
from app.schemas.payment import PaymentCreate


async def get_by_id(session: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def get_by_idempotency_key(session: AsyncSession, key: str) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.idempotency_key == key))
    return result.scalar_one_or_none()


async def create(session: AsyncSession, data: PaymentCreate, idempotency_key: str) -> Payment:
    payment = Payment(
        idempotency_key=idempotency_key,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        payment_metadata=data.metadata,
        webhook_url=str(data.webhook_url),
    )
    session.add(payment)
    await session.flush()
    session.add(Outbox(payment_id=payment.id))
    await session.commit()
    await session.refresh(payment)

    return payment
