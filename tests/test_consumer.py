# pylint: disable=unused-argument

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

import httpx

from app.db.models.payment import Currency, Payment, PaymentStatus
from app.workers.consumer.handler import process_payment
from app.workers.consumer.webhook import send_webhook

from app.settings.config import settings

from tests.conftest import make_payment


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=True)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=True)
async def test_process_payment_success_updates_status(mock_webhook, mock_emulate, factory):
    payment = await make_payment(factory)
    await process_payment(str(payment.id), factory)

    async with factory() as s:
        result = await s.execute(select(Payment).where(Payment.id == payment.id))
        updated = result.scalar_one()
    assert updated.status == PaymentStatus.succeeded
    assert updated.processed_at is not None


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=False)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=True)
async def test_process_payment_failure_updates_status(mock_webhook, mock_emulate, factory):
    payment = await make_payment(factory)
    await process_payment(str(payment.id), factory)

    async with factory() as s:
        result = await s.execute(select(Payment).where(Payment.id == payment.id))
        updated = result.scalar_one()
    assert updated.status == PaymentStatus.failed


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=True)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=True)
async def test_process_payment_calls_webhook_with_correct_payload(mock_webhook, mock_emulate, factory):
    payment = await make_payment(factory)
    await process_payment(str(payment.id), factory)

    mock_webhook.assert_called_once()
    payload = mock_webhook.call_args[0][1]
    assert payload["payment_id"] == str(payment.id)
    assert payload["status"] == PaymentStatus.succeeded.value
    assert payload["currency"] == Currency.RUB.value


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=True)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=False)
@patch("app.workers.consumer.handler.broker")
async def test_process_payment_publishes_to_dlq_on_webhook_failure(mock_broker, mock_webhook, mock_emulate, factory):
    mock_broker.publish = AsyncMock()
    payment = await make_payment(factory)
    await process_payment(str(payment.id), factory)

    mock_broker.publish.assert_called_once()
    call_kwargs = mock_broker.publish.call_args
    assert call_kwargs[1]["queue"] == "payments.dlq"
    assert call_kwargs[0][0]["payment_id"] == str(payment.id)


@patch("app.workers.consumer.handler._emulate_processing", new_callable=AsyncMock, return_value=True)
@patch("app.workers.consumer.handler.send_webhook", new_callable=AsyncMock, return_value=True)
@patch("app.workers.consumer.handler.broker")
async def test_process_payment_nonexistent_id_does_nothing(mock_broker, mock_webhook, mock_emulate, factory):
    mock_broker.publish = AsyncMock()
    await process_payment(str(uuid.uuid4()), factory)
    mock_webhook.assert_not_called()
    mock_broker.publish.assert_not_called()


@patch("httpx.AsyncClient.post")
async def test_send_webhook_success(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    result = await send_webhook("http://localhost:9999/webhook", {"payment_id": "123"})
    assert result is True
    assert mock_post.call_count == 1


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_send_webhook_retries_on_failure(mock_sleep):
    with patch("httpx.AsyncClient.post", AsyncMock(side_effect=httpx.NetworkError("connection error"))):
        result = await send_webhook("http://localhost:9999/webhook", {"payment_id": "123"})
    assert result is False
    assert mock_sleep.call_count == settings.webhook_retry_attempts - 1


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_send_webhook_exponential_backoff(mock_sleep):
    with patch("httpx.AsyncClient.post", AsyncMock(side_effect=Exception("connection error"))):
        await send_webhook("http://localhost:9999/webhook", {"payment_id": "123"})

    delays = [call.args[0] for call in mock_sleep.call_args_list]
    for i in range(1, len(delays)):
        assert delays[i] == delays[i - 1] * 2


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_send_webhook_succeeds_on_second_attempt(mock_sleep):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    side_effects = [httpx.NetworkError("first attempt fails"), mock_response]
    with patch("httpx.AsyncClient.post", AsyncMock(side_effect=side_effects)):
        result = await send_webhook("http://localhost:9999/webhook", {"payment_id": "123"})
    assert result is True
    assert mock_sleep.call_count == 1
