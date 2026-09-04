from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, Field

from services.payment_api.domain.payment import Currency, Payment, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount_minor: Annotated[int, Field(strict=True, gt=0)]
    currency: Currency


class PaymentResponse(BaseModel):
    id: UUID
    amount_minor: int
    currency: Currency
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, payment: Payment) -> Self:
        return cls(
            id=payment.id,
            amount_minor=payment.money.amount_minor,
            currency=payment.money.currency,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
