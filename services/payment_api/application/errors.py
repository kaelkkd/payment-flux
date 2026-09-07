from uuid import UUID


class PaymentNotFound(Exception):
    def __init__(self, payment_id: UUID) -> None:
        self.payment_id = payment_id
        super().__init__("Payment was not found.")
