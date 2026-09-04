def test_health_endpoint_returns_service_status(client) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "test-request"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request"
    assert response.json() == {
        "status": "ok",
        "service": "NEXUS API",
        "version": "0.1.0",
        "environment": "test",
    }
