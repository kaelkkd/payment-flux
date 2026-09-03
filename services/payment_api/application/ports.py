from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from services.payment_api.domain.payment import Payment


class PaymentRepository(Protocol):
    async def add(self, payment: Payment) -> None: ...

    async def get(self, payment_id: UUID) -> Payment | None: ...


class PaymentUnitOfWork(Protocol):
    payments: PaymentRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...


type PaymentUnitOfWorkFactory = Callable[[], PaymentUnitOfWork]
