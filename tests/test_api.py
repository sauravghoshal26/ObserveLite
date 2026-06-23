import os

os.environ["ENABLE_TRACING"] = "false"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ObserveLite"}


def test_predict_endpoint_positive_sentiment() -> None:
    response = client.post("/predict", json={"text": "This simple demo is great and reliable."})

    assert response.status_code == 200
    body = response.json()
    assert body["sentiment"] == "positive"
    assert body["confidence"] > 0.5
    assert body["input_length"] == len("This simple demo is great and reliable.")


def test_predict_endpoint_rejects_empty_text() -> None:
    response = client.post("/predict", json={"text": ""})

    assert response.status_code == 422


def test_metrics_endpoint_exposes_custom_metrics() -> None:
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "request_count_total" in response.text
    assert "request_latency_bucket" in response.text
