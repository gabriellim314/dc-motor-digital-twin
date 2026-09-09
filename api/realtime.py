"""Async WebSocket loop for live Digital Twin simulation."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

from api.service import MotorTwinService

LOGGER = logging.getLogger(__name__)


async def stream_simulation(
    websocket: WebSocket,
    service: MotorTwinService,
    dt: float = 0.01,
    interval: float = 0.05,
) -> None:
    """Send live simulation frames until the client disconnects or the sim stops."""
    await websocket.accept()

    if dt <= 0.0 or interval <= 0.0:
        await _send_status(websocket, "error", "invalid state")
        await _close(websocket, code=1008)
        return

    service.begin_live()
    try:
        while service.running:
            try:
                frame = await asyncio.to_thread(service.step_live, dt)
            except Exception:
                LOGGER.exception("Live simulation step failed")
                await _send_status(websocket, "error", "invalid state")
                break

            if frame is None:
                await _send_status(websocket, "error", "invalid state")
                break

            await websocket.send_json(frame)
            await asyncio.sleep(interval)

        await _send_status(websocket, "stopped")
    except WebSocketDisconnect:
        LOGGER.info("WebSocket client disconnected")
    finally:
        service.stop()
        await _close(websocket)


async def _send_status(websocket: WebSocket, status: str, detail: str | None = None) -> None:
    if websocket.client_state != WebSocketState.CONNECTED:
        return
    payload: dict[str, str] = {"status": status}
    if detail is not None:
        payload["detail"] = detail
    with contextlib.suppress(Exception):
        await websocket.send_json(payload)


async def _close(websocket: WebSocket, code: int = 1000) -> None:
    if websocket.client_state != WebSocketState.CONNECTED:
        return
    with contextlib.suppress(Exception):
        await websocket.close(code=code)
