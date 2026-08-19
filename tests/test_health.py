from fastapi.testclient import TestClient

from services.payment_api.main import app


def test_liveness_reports_healthy_process() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
