# -*- coding: utf-8 -*-
"""
Notification Routes - Rotas do Serviço de Notificações
Exporta routers de endpoints
"""

from routes.notification_config import router as config_router
from routes.notification_logs import router as logs_router

__all__ = ["config_router", "logs_router"]
