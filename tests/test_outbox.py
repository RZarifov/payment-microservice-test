import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.payment import Currency, Outbox, Payment, PaymentStatus
from app.workers.outbox.outbox_worker import _poll_once
from tests.conftest import test_engine, make_payment


@pytest_asyncio.fixture(loop_scope="session")
async def factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@patch("app.workers.outbox.outbox_worker.broker")
async def test_poll_publishes_pending_entry(mock_broker, factory):
    mock_broker.publish = AsyncMock()
    payment = await make_payment(factory)

    await _poll_once(factory)

    mock_broker.publish.assert_called_once_with(
        {"payment_id": str(payment.id)},
        queue="payments.new",
    )


@patch("app.workers.outbox.outbox_worker.broker")
async def test_poll_sets_published_at(mock_broker, factory, test_engine):
    mock_broker.publish = AsyncMock()
    payment = await make_payment(factory)

    await _poll_once(factory)

    async with factory() as s:
        from sqlalchemy import select
        result = await s.execute(select(Outbox).where(Outbox.payment_id == payment.id))
        entry = result.scalar_one()
    assert entry.published_at is not None


@patch("app.workers.outbox.outbox_worker.broker")
async def test_poll_skips_already_published(mock_broker, factory):
    mock_broker.publish = AsyncMock()
    async with factory() as s:
        payment = Payment(
            idempotency_key=str(uuid.uuid4()),
            amount=100,
            currency=Currency.RUB,
            description="test",
            webhook_url="http://localhost:9999/webhook",
            status=PaymentStatus.pending,
        )
        s.add(payment)
        await s.flush()
        s.add(Outbox(payment_id=payment.id, published_at=datetime.now(timezone.utc)))
        await s.commit()

    await _poll_once(factory)

    mock_broker.publish.assert_not_called()


@patch("app.workers.outbox.outbox_worker.broker")
async def test_poll_empty_outbox(mock_broker, factory):
    mock_broker.publish = AsyncMock()
    await _poll_once(factory)
    mock_broker.publish.assert_not_called()


@patch("app.workers.outbox.outbox_worker.broker")
async def test_poll_publishes_multiple_entries(mock_broker, factory):
    mock_broker.publish = AsyncMock()
    await make_payment(factory)
    await make_payment(factory)

    await _poll_once(factory)

    assert mock_broker.publish.call_count == 2
