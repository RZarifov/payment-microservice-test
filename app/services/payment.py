import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import payment as payment_crud

# ONLY FOR TYPES DISPLAY
from app.schemas.payment import PaymentCreate
from app.db.models.payment import Payment


async def get_payment(session: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    return await payment_crud.get_by_id(session, payment_id)


async def create_payment(session: AsyncSession, data: PaymentCreate, idempotency_key: str) -> Payment:
    existing = await payment_crud.get_by_idempotency_key(session, idempotency_key)
    if existing:
        return existing
    return await payment_crud.create(session, data, idempotency_key)
