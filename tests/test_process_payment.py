from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.workers.consumer.handler import process_payment

from app.db.models.payment import Payment, PaymentStatus

from tests.conftest import make_payment


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=False)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=True)
async def test_process_payment_failure_sets_processed_at(_, __, factory):
    payment = await make_payment(factory)
    await process_payment(str(payment.id), factory)

    async with factory() as s:
        result = await s.execute(select(Payment).where(Payment.id == payment.id))
        updated = result.scalar_one()
    assert updated.status == PaymentStatus.failed
    assert updated.processed_at is not None


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=True)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=False)
@patch("app.workers.consumer.handler.broker")
async def test_process_payment_dlq_payload_contains_reason(mock_broker, _, __, factory):
    mock_broker.publish = AsyncMock()
    payment = await make_payment(factory)
    await process_payment(str(payment.id), factory)

    call = mock_broker.publish.call_args
    assert call.kwargs["queue"] == "payments.dlq"
    assert call.args[0]["payment_id"] == str(payment.id)
    assert "reason" in call.args[0]
