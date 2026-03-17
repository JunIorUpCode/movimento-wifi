# -*- coding: utf-8 -*-
"""
Routes - Rotas da API do Event Service
"""

from .event import router as event_router
from .device_data import router as device_data_router

__all__ = ["event_router", "device_data_router"]
