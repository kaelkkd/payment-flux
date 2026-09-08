import pytest

from services.payment_api.application.services import PaymentService
from services.payment_api.domain.payment import Currency, PaymentStatus
from tests.mock_service import FakeUnitOfWork


@pytest.mark.asyncio
async def test_create_payment_adds_and_commits_payment() -> None:
    unit_of_work = FakeUnitOfWork()
    service = PaymentService(lambda: unit_of_work)

    payment = await service.create_payment(amount_minor=3500, currency=Currency.BRL)

    assert payment.status is PaymentStatus.PENDING
    assert payment.money.amount_minor == 3500
    assert payment.money.currency is Currency.BRL
    assert await unit_of_work.payments.get(payment.id) == payment
    assert unit_of_work.committed is True
