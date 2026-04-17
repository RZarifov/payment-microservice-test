import enum
import uuid
from datetime import datetime

from decimal import Decimal
from typing import Any

from sqlalchemy import Enum, ForeignKey, Numeric, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Currency(str, enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, enum.Enum):
    pending = "pending" # pylint: disable=invalid-name
    succeeded = "succeeded"  # pylint: disable=invalid-name
    failed = "failed"  # pylint: disable=invalid-name


class Payment(Base):
    __tablename__ = "payments"

    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="currency"))

    description: Mapped[str] = mapped_column(String)

    payment_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.pending
        )

    webhook_url: Mapped[str] = mapped_column(String)

    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Outbox(Base):
    __tablename__ = "outbox"

    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id"))

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
