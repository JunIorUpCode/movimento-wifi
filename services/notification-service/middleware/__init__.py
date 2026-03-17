# -*- coding: utf-8 -*-
"""
Notification Middleware - Middlewares do Serviço de Notificações
Exporta middlewares de autenticação e autorização
"""

from middleware.auth_middleware import require_tenant_auth, get_current_tenant

__all__ = ["require_tenant_auth", "get_current_tenant"]
