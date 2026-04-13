import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.payment import Outbox, Payment, Currency, PaymentStatus
from tests.conftest import AUTH_HEADERS, IDEM_HEADERS, PAYMENT_BODY


async def test_create_payment_returns_202(client: AsyncClient):
    response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    assert response.status_code == 202


async def test_create_payment_response_shape(client: AsyncClient):
    response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    data = response.json()
    assert "id" in data
    assert data["status"] == PaymentStatus.pending
    assert data["amount"] == "100.00"
    assert data["currency"] == "RUB"
    assert data["description"] == "test payment"
    assert data["webhook_url"] == "http://localhost:9999/webhook"
    assert "created_at" in data
    assert data["processed_at"] is None


async def test_create_payment_idempotency_returns_same_payment(client: AsyncClient):
    r1 = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    r2 = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r1.json()["id"] == r2.json()["id"]


async def test_create_payment_idempotency_creates_single_outbox_entry(client: AsyncClient, test_engine):
    await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    async with async_sessionmaker(test_engine, expire_on_commit=False)() as s:
        result = await s.execute(select(Outbox))
        assert len(result.scalars().all()) == 1


async def test_create_payment_different_idempotency_keys_create_different_payments(client: AsyncClient):
    r1 = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers={**IDEM_HEADERS, "Idempotency-Key": "key-1"})
    r2 = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers={**IDEM_HEADERS, "Idempotency-Key": "key-2"})
    assert r1.json()["id"] != r2.json()["id"]


async def test_create_payment_missing_api_key_returns_422(client: AsyncClient):
    headers = {"Idempotency-Key": "test-002"}
    response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=headers)
    assert response.status_code == 422


async def test_create_payment_wrong_api_key_returns_401(client: AsyncClient):
    headers = {**IDEM_HEADERS, "X-API-Key": "wrong-key"}
    response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=headers)
    assert response.status_code == 401


async def test_create_payment_missing_idempotency_key_returns_422(client: AsyncClient):
    response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=AUTH_HEADERS)
    assert response.status_code == 422


async def test_create_payment_invalid_currency_returns_422(client: AsyncClient):
    body = {**PAYMENT_BODY, "currency": "GBP"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_missing_required_fields_returns_422(client: AsyncClient):
    response = await client.post("/api/v1/payments", json={}, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_creates_outbox_entry(client: AsyncClient, test_engine):
    await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    async with async_sessionmaker(test_engine, expire_on_commit=False)() as s:
        result = await s.execute(select(Outbox))
        entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].published_at is None


async def test_get_payment_returns_200(client: AsyncClient):
    create_response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    payment_id = create_response.json()["id"]
    response = await client.get(f"/api/v1/payments/{payment_id}", headers=AUTH_HEADERS)
    assert response.status_code == 200


async def test_get_payment_returns_correct_data(client: AsyncClient):
    create_response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    payment_id = create_response.json()["id"]
    response = await client.get(f"/api/v1/payments/{payment_id}", headers=AUTH_HEADERS)
    assert response.json()["id"] == payment_id


async def test_get_payment_not_found_returns_404(client: AsyncClient):
    response = await client.get(
        "/api/v1/payments/00000000-0000-0000-0000-000000000000",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


async def test_get_payment_missing_api_key_returns_422(client: AsyncClient):
    response = await client.get("/api/v1/payments/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 422


async def test_get_payment_wrong_api_key_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/payments/00000000-0000-0000-0000-000000000000",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


async def test_get_payment_invalid_uuid_returns_422(client: AsyncClient):
    response = await client.get("/api/v1/payments/not-a-uuid", headers=AUTH_HEADERS)
    assert response.status_code == 422


async def test_create_payment_negative_amount_returns_422(client: AsyncClient):
    body = {**PAYMENT_BODY, "amount": "-100.00"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_zero_amount_returns_422(client: AsyncClient):
    body = {**PAYMENT_BODY, "amount": "0.00"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_missing_amount_returns_422(client: AsyncClient):
    body = {k: v for k, v in PAYMENT_BODY.items() if k != "amount"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_missing_webhook_url_returns_422(client: AsyncClient):
    body = {k: v for k, v in PAYMENT_BODY.items() if k != "webhook_url"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_missing_currency_returns_422(client: AsyncClient):
    body = {k: v for k, v in PAYMENT_BODY.items() if k != "currency"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_missing_description_returns_422(client: AsyncClient):
    body = {k: v for k, v in PAYMENT_BODY.items() if k != "description"}
    response = await client.post("/api/v1/payments", json=body, headers=IDEM_HEADERS)
    assert response.status_code == 422


async def test_create_payment_outbox_linked_to_correct_payment(client: AsyncClient, test_engine):
    response = await client.post("/api/v1/payments", json=PAYMENT_BODY, headers=IDEM_HEADERS)
    payment_id = response.json()["id"]
    async with async_sessionmaker(test_engine, expire_on_commit=False)() as s:
        result = await s.execute(select(Outbox))
        entry = result.scalars().first()
    assert str(entry.payment_id) == payment_id


async def test_payment_created_at_set_by_database(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
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
        await s.commit()
        await s.refresh(payment)
        assert payment.created_at is not None
        assert payment.created_at.tzinfo is not None
