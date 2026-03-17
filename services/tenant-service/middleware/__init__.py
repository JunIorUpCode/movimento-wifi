# -*- coding: utf-8 -*-
"""
Middleware - Middlewares do tenant-service
"""

from middleware.auth_middleware import require_admin

__all__ = ["require_admin"]
