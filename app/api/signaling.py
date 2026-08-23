import json
from typing import Optional, Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect, APIRouter

router = APIRouter(tags=["signaling"])

# Shared in-memory room state (per session).
# Structure: {session_id: {"participants": set(), "offer": Optional[str], "answer": Optional[str], "candidates": List[Dict]}}
rooms: Dict[str, Dict[str, Any]] = {}


def _get_room(session_id: str) -> Dict[str, Any]:
    """Get or create a room for the given session ID."""
    if session_id not in rooms:
        rooms[session_id] = {
            "participants": set(),
            "offer": None,
            "answer": None,
            "candidates": [],
        }
    return rooms[session_id]


@router.websocket("/signaling/{session_id}")
async def signaling_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    room = _get_room(session_id)
    room["participants"].add("client")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "msg": "invalid JSON"}))
                continue

            msg_type = msg.get("type")
            if msg_type == "offer":
                sdp = msg.get("sdp")
                room["offer"] = sdp
                # Acknowledge offer locally; in full setup forward to peer WS.
                await websocket.send_text(json.dumps({"type": "offer_accepted", "sdp": sdp}))

            elif msg_type == "answer":
                sdp = msg.get("sdp")
                room["answer"] = sdp
                await websocket.send_text(json.dumps({"type": "answer_accepted", "sdp": sdp}))

            elif msg_type == "candidate":
                candidate = msg.get("candidate")
                room["candidates"].append(candidate)
                await websocket.send_text(json.dumps({"type": "candidate_acked", "candidate": candidate}))

            else:
                await websocket.send_text(json.dumps({"type": "error", "msg": f"unknown type: {msg_type}"}))

    except WebSocketDisconnect:
        room["participants"].discard("client")
        if not room["participants"]:
            rooms.pop(session_id, None)