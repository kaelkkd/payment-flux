from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from services.payment_api.main import create_app
from tests.mock_service import FakeUnitOfWork


def test_post_then_get_returns_same_payment() -> None:
    unit_of_work = FakeUnitOfWork()
    app = create_app(unit_of_work_factory=lambda: unit_of_work)

    with TestClient(app) as client:
        created = client.post("/v1/payments", json={"amount_minor": 3500, "currency": "BRL"})

        assert created.status_code == 201
        body = created.json()
        assert body["amount_minor"] == 3500
        assert body["currency"] == "BRL"
        assert body["status"] == "PENDING"
        assert body["created_at"] == body["updated_at"]

        fetched = client.get(f"/v1/payments/{body['id']}")

    assert fetched.status_code == 200
    assert fetched.json() == body
    assert unit_of_work.committed is True


def test_get_missing_payment_returns_404() -> None:
    unit_of_work = FakeUnitOfWork()
    app = create_app(unit_of_work_factory=lambda: unit_of_work)

    with TestClient(app) as client:
        response = client.get(f"/v1/payments/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "PAYMENT_NOT_FOUND", "message": "Payment was not found."}
    }
    assert unit_of_work.committed is False


@pytest.mark.parametrize(
    "payload",
    [
        {"amount_minor": 0, "currency": "BRL"},
        {"amount_minor": -1, "currency": "BRL"},
        {"amount_minor": 1.5, "currency": "BRL"},
        {"amount_minor": True, "currency": "BRL"},
        {"amount_minor": "100", "currency": "BRL"},
        {"amount_minor": 100, "currency": "EUR"},
        {"currency": "BRL"},
    ],
)
def test_invalid_payment_request_is_rejected(payload: dict[str, object]) -> None:
    unit_of_work = FakeUnitOfWork()
    app = create_app(unit_of_work_factory=lambda: unit_of_work)

    with TestClient(app) as client:
        response = client.post("/v1/payments", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "INVALID_REQUEST", "message": "The request is invalid."}
    }
    assert unit_of_work.entered is False
    assert unit_of_work.committed is False


def test_invalid_payment_id_is_rejected_before_lookup() -> None:
    unit_of_work = FakeUnitOfWork()
    app = create_app(unit_of_work_factory=lambda: unit_of_work)

    with TestClient(app) as client:
        response = client.get("/v1/payments/not-a-uuid")

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "INVALID_REQUEST", "message": "The request is invalid."}
    }
    assert unit_of_work.entered is False
    assert unit_of_work.committed is False


def test_malformed_json_returns_stable_validation_error() -> None:
    unit_of_work = FakeUnitOfWork()
    app = create_app(unit_of_work_factory=lambda: unit_of_work)

    with TestClient(app) as client:
        response = client.post(
            "/v1/payments", content='{"amount_minor":', headers={"Content-Type": "application/json"}
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "The request is invalid.",
        }
    }
    assert unit_of_work.entered is False


def test_payments_routes_document_error_response() -> None:
    app = create_app(unit_of_work_factory=FakeUnitOfWork)
    schema = app.openapi()
    post_responses = schema["paths"]["/v1/payments"]["post"]["responses"]
    get_responses = schema["paths"]["/v1/payments/{payment_id}"]["get"]["responses"]

    assert "422" in post_responses
    assert "404" in get_responses
    assert "422" in get_responses
