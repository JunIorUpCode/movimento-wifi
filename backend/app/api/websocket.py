"""
WebSocket endpoint para atualizações em tempo real.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.monitor_service import monitor_service

ws_router = APIRouter()


@ws_router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """WebSocket para receber atualizações em tempo real do monitoramento."""
    await websocket.accept()
    monitor_service.register_ws(websocket)
    try:
        while True:
            # Mantém a conexão aberta esperando mensagens do cliente
            data = await websocket.receive_text()
            # Permite que o cliente envie comandos (futuro)
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        monitor_service.unregister_ws(websocket)
