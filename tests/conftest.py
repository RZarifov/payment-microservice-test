# pylint: disable=redefined-outer-name

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db

from app.db.base import Base
from app.db.models.payment import Payment, PaymentStatus, Currency, Outbox

from app.main import app
from app.settings.config import settings


TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/luna_test_test"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    admin_engine = create_async_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'luna_test_test'"))
        if not result.scalar():
            await conn.execute(text("CREATE DATABASE luna_test_test"))
    await admin_engine.dispose()

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def make_payment(factory: async_sessionmaker) -> Payment:
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
        s.add(Outbox(payment_id=payment.id))
        await s.commit()
        await s.refresh(payment)
        return payment


@pytest_asyncio.fixture(loop_scope="session")
async def factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


PAYMENT_BODY = {
    "amount": "100.00",
    "currency": "RUB",
    "description": "test payment",
    "webhook_url": "http://localhost:9999/webhook",
}


AUTH_HEADERS = {"X-API-Key": "luna_test"}
IDEM_HEADERS = {**AUTH_HEADERS, "Idempotency-Key": "test-001"}
