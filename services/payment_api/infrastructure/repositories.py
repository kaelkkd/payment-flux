from datetime import UTC
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.payment_api.domain.payment import Currency, Money, Payment, PaymentStatus
from services.payment_api.infrastructure.models import PaymentRecord


def payment_to_record(payment: Payment) -> PaymentRecord:
    return PaymentRecord(
        id=payment.id,
        amount_minor=payment.money.amount_minor,
        currency=payment.money.currency.value,
        status=payment.status.value,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def payment_from_record(record: PaymentRecord) -> Payment:
    return Payment(
        id=record.id,
        money=Money(
            amount_minor=record.amount_minor,
            currency=Currency(record.currency),
        ),
        status=PaymentStatus(record.status),
        created_at=record.created_at.astimezone(UTC),
        updated_at=record.updated_at.astimezone(UTC),
    )


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, payment: Payment) -> None:
        self._session.add(payment_to_record(payment))

    async def get(self, payment_id: UUID) -> Payment | None:
        record = await self._session.get(PaymentRecord, payment_id)

        if record is None:
            return None

        return payment_from_record(record)
