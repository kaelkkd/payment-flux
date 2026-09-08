from types import TracebackType
from typing import Self
from uuid import UUID

from services.payment_api.application.ports import PaymentRepository
from services.payment_api.domain.payment import Payment


class FakePaymentRepository:
    def __init__(self) -> None:
        self.payments: dict[UUID, Payment] = {}

    async def add(self, payment: Payment) -> None:
        self.payments[payment.id] = payment

    async def get(self, payment_id: UUID) -> Payment | None:
        return self.payments.get(payment_id)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.payments: PaymentRepository = FakePaymentRepository()
        self.committed = False
        self.entered = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True
