"""Endpoint tests for TURN credential distribution."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


class TestTurnCredentialsEndpoint:
    def test_returns_credentials_when_turn_configured(self, client):
        with patch("app.api.transfers.settings") as mock_settings:
            mock_settings.TURN_URLS = "turn:turn.lynkshare.app:3478"
            mock_settings.TURN_SECRET = "endpoint-secret"
            resp = client.get("/api/v1/transfers/some-id/turn-credentials")

        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert body["urls"] == ["turn:turn.lynkshare.app:3478"]
        assert "username" in body and "credential" in body
        assert "endpoint-secret" not in resp.text

    def test_disabled_when_turn_not_configured(self, client):
        with patch("app.api.transfers.settings") as mock_settings:
            mock_settings.TURN_URLS = ""
            mock_settings.TURN_SECRET = ""
            resp = client.get("/api/v1/transfers/some-id/turn-credentials")

        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
