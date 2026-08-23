import json
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["signaling"])

# session_id -> room state. The server is a *dumb relay*: it forwards every
# valid JSON object to the other peers and buffers a bounded history so a
# peer that joins late (receiver after sender) still receives the offer.
rooms: Dict[str, Dict[str, Any]] = {}

_HISTORY_CAP = 100


def _get_room(session_id: str) -> Dict[str, Any]:
    if session_id not in rooms:
        rooms[session_id] = {"members": [], "history": []}
    return rooms[session_id]


@router.websocket("/signaling/{session_id}")
async def signaling_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    room = _get_room(session_id)

    # Replay buffered history to the late joiner (sender may have signaled
    # before the receiver connected).
    for frame in list(room["history"]):
        await websocket.send_text(frame)
    room["members"].append(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                decoded = json.loads(raw)
                if not isinstance(decoded, dict):
                    raise ValueError("not an object")
            except (json.JSONDecodeError, ValueError):
                await websocket.send_text(
                    json.dumps({"type": "error", "msg": "invalid JSON"})
                )
                continue

            # Buffer once, then fan out to everyone else.
            room["history"].append(raw)
            if len(room["history"]) > _HISTORY_CAP:
                del room["history"][: len(room["history"]) - _HISTORY_CAP]
            for peer in list(room["members"]):
                if peer is not websocket:
                    await peer.send_text(raw)

    except WebSocketDisconnect:
        room["members"] = [m for m in room["members"] if m is not websocket]
        if not room["members"]:
            rooms.pop(session_id, None)
