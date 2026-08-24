"""TURN short-lived credential minting (coturn use-auth-secret scheme).

The shared secret lives only in the backend environment. Clients receive
time-limited HMAC credentials so a leaked credential expires on its own
(POTENTIAL_ISSUES #18 mitigation).
"""

import base64
import hashlib
import hmac
import time

DEFAULT_TTL_SECONDS = 600


def generate_turn_credentials(
    secret: str,
    session_id: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
) -> dict:
    """Build coturn REST-style credentials.

    username   = "<unix_expiry>:<session_id>"
    credential = base64(HMAC-SHA1(secret, username))
    """
    expiry = int(now if now is not None else time.time()) + ttl_seconds
    username = f"{expiry}:{session_id}"
    digest = hmac.new(secret.encode(), username.encode(), hashlib.sha1).digest()
    return {
        "username": username,
        "credential": base64.b64encode(digest).decode(),
        "ttl": ttl_seconds,
    }
