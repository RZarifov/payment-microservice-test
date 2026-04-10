import uuid
from datetime import datetime
# NOTE: EVERYTHING SHOULD BE DECIMAL IF WE CARE FOR FLOAT ERROR, ESPECIALLY IN FINANCES
from decimal import Decimal
# NOTE: Any FOR NOW. IF NECESSARY WILL BE MORE GRANULAR IN THE FUTURE
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.payment import Currency, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None = None
    webhook_url: str


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: PaymentStatus
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None = Field(None, validation_alias="payment_metadata")
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
