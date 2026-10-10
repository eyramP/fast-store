from fastapi.testclient import TestClient
from user_service.main import app

client = TestClient(app)
def test_liveness_probe():
    response = client.get("/health/liveness")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}