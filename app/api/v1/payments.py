import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment import create_payment, get_payment


router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# NOTE: 202 IS DELIBERATE. BECAUSE THE CREATION PROCESS IS ONGOING IN THE BACKGROUND
@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=PaymentResponse)
async def create_payment_endpoint(
    data: PaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    return await create_payment(session, data, idempotency_key)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_endpoint(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    payment = await get_payment(session, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
