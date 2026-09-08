"""Frontend serving tests.

The NEXUS frontend prototype (``frontend/public``) is the visual contract and
is served by the FastAPI application without any redesign.
"""


def test_index_serves_nexus_frontend(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "NEXUS / Engineering Intelligence" in response.text


def test_static_stylesheet_is_served(client) -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.text.startswith(":root{")


def test_static_app_script_is_served(client) -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert 'const API_BASE = "/api/v1";' in response.text