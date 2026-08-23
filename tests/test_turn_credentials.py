"""TURN short-lived credential tests.

Coturn `use-auth-secret` scheme (RFC-style REST API):
- username  = "<unix_expiry>:<session_id>"
- credential = base64(HMAC-SHA1(secret, username))
The shared secret must NEVER appear in any API response.
"""
import base64
import hashlib
import hmac

from app.services.turn_service import generate_turn_credentials


class TestGenerateTurnCredentials:
    def test_credential_matches_hmac_sha1_scheme(self):
        creds = generate_turn_credentials(
            secret="test-secret", session_id="sess-1", ttl_seconds=600, now=1000.0
        )

        expected_username = "1600:sess-1"
        expected_cred = base64.b64encode(
            hmac.new(b"test-secret", expected_username.encode(), hashlib.sha1).digest()
        ).decode()

        assert creds["username"] == expected_username
        assert creds["credential"] == expected_cred
        assert creds["ttl"] == 600

    def test_username_embeds_absolute_expiry(self):
        creds = generate_turn_credentials(
            secret="s", session_id="abc", ttl_seconds=60, now=5000.0
        )
        assert creds["username"].startswith("5060:abc")

    def test_different_sessions_yield_different_credentials(self):
        a = generate_turn_credentials("s", "a", now=0.0)
        b = generate_turn_credentials("s", "b", now=0.0)
        assert a["credential"] != b["credential"]

    def test_secret_never_appears_in_serialized_response(self):
        import json

        secret = "super-secret-turn-key"
        creds = generate_turn_credentials(secret, "sess-x", now=0.0)
        blob = json.dumps(creds)
        assert secret not in blob
