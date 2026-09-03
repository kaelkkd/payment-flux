from datetime import UTC, datetime
from typing import cast
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from services.payment_api.domain.errors import (
    InvalidMoney,
    InvalidPaymentTimestamp,
    InvalidPaymentTransition,
)
from services.payment_api.domain.payment import Currency, Money, Payment, PaymentStatus


def test_create_payment_starts_pending() -> None:
    payment_id = UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790")
    timestamp = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    money = Money(amount_minor=3500, currency=Currency.BRL)

    payment = Payment.create(money, payment_id=payment_id, occurred_at=timestamp)

    assert payment.id == payment_id
    assert payment.money == money
    assert payment.status is PaymentStatus.PENDING
    assert payment.created_at == timestamp
    assert payment.updated_at == timestamp


def test_money_rejects_zero_amount() -> None:
    with pytest.raises(InvalidMoney):
        Money(amount_minor=0, currency=Currency.BRL)


def test_money_rejects_non_integer_amount() -> None:
    with pytest.raises(InvalidMoney):
        Money(amount_minor=cast(int, 3500.5), currency=Currency.BRL)


def test_money_rejects_invalid_currency() -> None:
    with pytest.raises(InvalidMoney):
        Money(amount_minor=3500, currency=cast(Currency, "EUR"))


def test_create_payment_rejects_timezone_unaware_timestamp() -> None:
    money = Money(amount_minor=3500, currency=Currency.BRL)

    with pytest.raises(InvalidPaymentTimestamp):
        Payment.create(money, occurred_at=datetime(2026, 8, 31, 12, 0).replace(tzinfo=None))


def test_payment_rejects_naive_created_timestamp() -> None:
    money = Money(amount_minor=3500, currency=Currency.BRL)

    with pytest.raises(InvalidPaymentTimestamp):
        Payment(
            id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
            money=money,
            status=PaymentStatus.PENDING,
            created_at=datetime(2026, 8, 31, 12, 0),
            updated_at=datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
        )


def test_payment_rejects_non_utc_timestamp() -> None:
    money = Money(amount_minor=3500, currency=Currency.BRL)
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=ZoneInfo("America/Sao_Paulo"),
    )

    with pytest.raises(InvalidPaymentTimestamp):
        Payment(
            id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
            money=money,
            status=PaymentStatus.PENDING,
            created_at=timestamp,
            updated_at=timestamp,
        )


def test_payment_rejects_updated_before_created() -> None:
    money = Money(amount_minor=3500, currency=Currency.BRL)
    created_at = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    updated_at = datetime(2026, 8, 31, 11, 0, tzinfo=UTC)

    with pytest.raises(InvalidPaymentTimestamp):
        Payment(
            id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
            money=money,
            status=PaymentStatus.PENDING,
            created_at=created_at,
            updated_at=updated_at,
        )


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    [
        (PaymentStatus.PENDING, PaymentStatus.RISK_REVIEW),
        (PaymentStatus.RISK_REVIEW, PaymentStatus.APPROVED),
        (PaymentStatus.RISK_REVIEW, PaymentStatus.REJECTED),
    ],
)
def test_payment_allows_valid_transition(
    initial_status: PaymentStatus, target_status: PaymentStatus
) -> None:
    initial_time = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    transition_time = datetime(2026, 9, 1, 12, 1, tzinfo=UTC)

    payment = Payment(
        id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
        money=Money(amount_minor=3500, currency=Currency.BRL),
        status=initial_status,
        created_at=initial_time,
        updated_at=initial_time,
    )

    transitioned = payment.transition_to(target_status, occurred_at=transition_time)

    assert transitioned.status is target_status
    assert transitioned.updated_at == transition_time
    assert payment.status is initial_status
    assert payment.updated_at == initial_time


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    [
        (PaymentStatus.PENDING, PaymentStatus.PENDING),
        (PaymentStatus.PENDING, PaymentStatus.APPROVED),
        (PaymentStatus.PENDING, PaymentStatus.REJECTED),
        (PaymentStatus.APPROVED, PaymentStatus.REJECTED),
        (PaymentStatus.REJECTED, PaymentStatus.APPROVED),
    ],
)
def test_payment_rejects_invalid_transition(
    initial_status: PaymentStatus, target_status: PaymentStatus
) -> None:
    timestamp = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    payment = Payment(
        id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
        money=Money(amount_minor=3500, currency=Currency.BRL),
        status=initial_status,
        created_at=timestamp,
        updated_at=timestamp,
    )

    with pytest.raises(InvalidPaymentTransition):
        payment.transition_to(target_status, occurred_at=datetime(2026, 9, 1, 12, 1, tzinfo=UTC))


def test_payment_rejects_transition_before_last_update() -> None:
    timestamp = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    payment = Payment(
        id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
        money=Money(amount_minor=3500, currency=Currency.BRL),
        status=PaymentStatus.PENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )

    with pytest.raises(InvalidPaymentTimestamp):
        payment.transition_to(
            PaymentStatus.RISK_REVIEW,
            occurred_at=datetime(2026, 9, 1, 11, 59, tzinfo=UTC),
        )


def test_payment_rejects_non_utc_transition_timestamp() -> None:
    timestamp = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    payment = Payment(
        id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
        money=Money(amount_minor=3500, currency=Currency.BRL),
        status=PaymentStatus.PENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )

    with pytest.raises(InvalidPaymentTimestamp):
        payment.transition_to(
            PaymentStatus.RISK_REVIEW,
            occurred_at=datetime(2026, 9, 1, 12, 1, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )


def test_payment_rejects_naive_transition_timestamp() -> None:
    timestamp = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    payment = Payment(
        id=UUID("f524c83a-64d6-4d5a-a7ec-1a5fcafba790"),
        money=Money(amount_minor=3500, currency=Currency.BRL),
        status=PaymentStatus.PENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )

    with pytest.raises(InvalidPaymentTimestamp):
        payment.transition_to(
            PaymentStatus.RISK_REVIEW,
            occurred_at=datetime(2026, 9, 1, 12, 1),
        )
