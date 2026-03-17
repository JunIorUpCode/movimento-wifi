# -*- coding: utf-8 -*-
"""
Módulo de Cliente API
Gerencia comunicação HTTP e WebSocket com o backend central
"""

from agent.api_client.http_client import HTTPClient
from agent.api_client.websocket_client import WebSocketClient

__all__ = ["HTTPClient", "WebSocketClient"]
