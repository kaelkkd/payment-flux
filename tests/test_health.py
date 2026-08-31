from fastapi.testclient import TestClient

from services.payment_api.main import create_app


def test_liveness_reports_healthy_process() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health/live")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

