from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from services.payment_api.domain.errors import (
    InvalidMoney,
    InvalidPaymentTimestamp,
    InvalidPaymentTransition,
)


class Currency(StrEnum):
    BRL = "BRL"
    USD = "USD"
    JPY = "JPY"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    RISK_REVIEW = "RISK_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


ALLOWED_TRANSITIONS: dict[
    PaymentStatus,
    frozenset[PaymentStatus],
] = {
    PaymentStatus.PENDING: frozenset({PaymentStatus.RISK_REVIEW}),
    PaymentStatus.RISK_REVIEW: frozenset(
        {
            PaymentStatus.APPROVED,
            PaymentStatus.REJECTED,
        }
    ),
    PaymentStatus.APPROVED: frozenset(),
    PaymentStatus.REJECTED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Money:
    amount_minor: int
    currency: Currency

    def __post_init__(self) -> None:
        if type(self.amount_minor) is not int:
            raise InvalidMoney(
                "Amount must be an integer representing the minor unit of the currency."
            )

        if self.amount_minor <= 0:
            raise InvalidMoney(
                "Amount must be a positive integer representing the minor unit of the currency."
            )

        if not isinstance(self.currency, Currency):
            raise InvalidMoney("Currency must be a valid Currency enum value.")


@dataclass(frozen=True, slots=True)
class Payment:
    id: UUID
    money: Money
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for timestamp in (self.created_at, self.updated_at):
            if timestamp.utcoffset() is None:
                raise InvalidPaymentTimestamp("Timestamps must be timezone-aware.")

            if timestamp.utcoffset() != timedelta(0):
                raise InvalidPaymentTimestamp("Timestamps must be in UTC.")

        if self.updated_at < self.created_at:
            raise InvalidPaymentTimestamp("Updated timestamp cannot precede creation timestamp.")

    @classmethod
    def create(
        cls, money: Money, *, payment_id: UUID | None = None, occurred_at: datetime | None = None
    ) -> "Payment":
        timestamp = occurred_at if occurred_at is not None else datetime.now(UTC)

        if timestamp.utcoffset() is None:
            raise InvalidPaymentTimestamp("Creation timestamps must be timezone-aware.")

        timestamp = timestamp.astimezone(UTC)

        return cls(
            id=payment_id if payment_id is not None else uuid4(),
            money=money,
            status=PaymentStatus.PENDING,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition_to(
        self,
        target: PaymentStatus,
        *,
        occurred_at: datetime,
    ) -> "Payment":
        if occurred_at.utcoffset() is None:
            raise InvalidPaymentTimestamp("Transitions timestamp must be timezone-aware.")

        if occurred_at.utcoffset() != timedelta(0):
            raise InvalidPaymentTimestamp("Transitions timestamp must be in UTC.")

        if occurred_at < self.updated_at:
            raise InvalidPaymentTimestamp(
                "Transition timestamp cannot precede the last update timestamp."
            )

        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidPaymentTransition(f"Cannot transition from {self.status} to {target}.")

        return replace(self, status=target, updated_at=occurred_at)
