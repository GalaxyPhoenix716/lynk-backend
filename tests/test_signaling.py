"""Signaling WebSocket tests — two-party fan-out + late-joiner replay.

Contract (Phases.md): the server is a dumb relay for `offer`, `answer` and
`candidate` JSON between the two peers of a session room. Messages are
buffered per room and replayed to a peer that joins late, so the sender may
signal its offer before the receiver has connected.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


class TestTwoPartyRelay:
    def test_offer_relays_from_sender_to_receiver(self, client):
        with client.websocket_connect("/ws/signaling/relay-1") as a:
            a.send_json({"type": "offer", "sdp": "sdp-from-a"})
            with client.websocket_connect("/ws/signaling/relay-1") as b:
                # Late joiner gets the buffered offer replayed on connect.
                assert b.receive_json() == {"type": "offer", "sdp": "sdp-from-a"}
                # And the sender receives nothing on its own socket.
                a.send_json({"type": "ping-probe"})
                assert b.receive_json() == {"type": "ping-probe"}

    def test_answer_and_candidates_relay_both_ways(self, client):
        with client.websocket_connect("/ws/signaling/relay-2") as a:
            with client.websocket_connect("/ws/signaling/relay-2") as b:
                a.send_json({"type": "offer", "sdp": "o"})
                assert b.receive_json() == {"type": "offer", "sdp": "o"}

                b.send_json({"type": "answer", "sdp": "ans"})
                assert a.receive_json() == {"type": "answer", "sdp": "ans"}

                cand = {
                    "type": "candidate",
                    "candidate": {"candidate": "c1", "sdpMid": "0"},
                }
                b.send_json(cand)
                assert a.receive_json() == cand

    def test_invalid_json_gets_error_on_sender_socket_only(self, client):
        with client.websocket_connect("/ws/signaling/relay-3") as a:
            with client.websocket_connect("/ws/signaling/relay-3") as b:
                a.send_text("not-json{")
                err = a.receive_json()
                assert err["type"] == "error"
                assert "invalid JSON" in err["msg"]
                # The malformed frame is NOT relayed or buffered: probe with a
                # valid frame and confirm the peer sees exactly that one.
                a.send_json({"type": "candidate", "candidate": {"candidate": "c"}})
                assert b.receive_json()["type"] == "candidate"

    def test_replay_contains_buffered_history_in_order(self, client):
        with client.websocket_connect("/ws/signaling/relay-4") as a:
            a.send_json({"type": "offer", "sdp": "first"})
            a.send_json(
                {
                    "type": "candidate",
                    "candidate": {"candidate": "cand-1", "sdpMid": "0"},
                }
            )
            with client.websocket_connect("/ws/signaling/relay-4") as b:
                assert b.receive_json() == {"type": "offer", "sdp": "first"}
                assert b.receive_json() == {
                    "type": "candidate",
                    "candidate": {"candidate": "cand-1", "sdpMid": "0"},
                }

    def test_room_survives_one_peer_disconnecting(self, client):
        with client.websocket_connect("/ws/signaling/relay-5") as a:
            a.send_json({"type": "offer", "sdp": "pre"})
            b_ctx = client.websocket_connect("/ws/signaling/relay-5")
            b = b_ctx.__enter__()
            try:
                assert b.receive_json()["type"] == "offer"
            finally:
                b_ctx.__exit__(None, None, None)
            # A stays connected; room must not be dropped. New joiner replays.
            with client.websocket_connect("/ws/signaling/relay-5") as c:
                assert c.receive_json() == {"type": "offer", "sdp": "pre"}
