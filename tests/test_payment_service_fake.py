from uuid import uuid4

import pytest

from services.payment_api.application.errors import PaymentNotFound
from services.payment_api.application.services import PaymentService
from services.payment_api.domain.payment import Currency, Money, Payment
from tests.mock_service import FakeUnitOfWork


@pytest.mark.asyncio
async def test_get_payment_returns_stored_payment_without_committing() -> None:
    unit_of_work = FakeUnitOfWork()
    payment = Payment.create(Money(3500, Currency.BRL))
    await unit_of_work.payments.add(payment)
    service = PaymentService(lambda: unit_of_work)
    result = await service.get_payment(payment.id)

    assert result == payment
    assert unit_of_work.committed is False


@pytest.mark.asyncio
async def test_get_missing_payment_raises_payment_not_found() -> None:
    unit_of_work = FakeUnitOfWork()
    service = PaymentService(lambda: unit_of_work)
    payment_id = uuid4()

    with pytest.raises(PaymentNotFound) as error:
        await service.get_payment(payment_id)

    assert error.value.payment_id == payment_id
    assert unit_of_work.committed is False
