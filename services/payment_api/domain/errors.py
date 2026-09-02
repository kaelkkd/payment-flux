class PaymentDomainError(Exception):
    pass


class InvalidMoney(PaymentDomainError):
    pass


class InvalidPaymentTimestamp(PaymentDomainError):
    pass


class InvalidPaymentTransition(PaymentDomainError):
    pass
