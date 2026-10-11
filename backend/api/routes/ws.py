"""WebSocket routes — real-time event streaming for CodeSentinel AI."""
from __future__ import annotations

from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

connected_clients: Set[WebSocket] = set()

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/events")
async def websocket_events(websocket: WebSocket) -> None:
    """Accept a WebSocket connection and stream live CodeSentinel events."""
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        await websocket.send_json(
            {"type": "connected", "message": "CodeSentinel live stream ready"}
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)


async def broadcast(event: dict) -> None:
    """Send an event dict to every connected WebSocket client.

    Dead sockets are silently removed from the set.
    """
    for ws in connected_clients.copy():
        try:
            await ws.send_json(event)
        except (WebSocketDisconnect, Exception):
            connected_clients.discard(ws)
