from uuid import UUID

from services.payment_api.application.errors import PaymentNotFound
from services.payment_api.application.ports import PaymentUnitOfWorkFactory
from services.payment_api.domain.payment import Currency, Money, Payment


class PaymentService:
    def __init__(self, unit_of_work_factory: PaymentUnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def create_payment(
        self,
        *,
        amount_minor: int,
        currency: Currency,
    ) -> Payment:
        money = Money(amount_minor=amount_minor, currency=currency)
        payment = Payment.create(money=money)

        async with self._unit_of_work_factory() as unit_of_work:
            await unit_of_work.payments.add(payment)
            await unit_of_work.commit()

        return payment

    async def get_payment(self, payment_id: UUID) -> Payment:
        async with self._unit_of_work_factory() as unit_of_work:
            payment = await unit_of_work.payments.get(payment_id)

            if payment is None:
                raise PaymentNotFound(payment_id)

        return payment
