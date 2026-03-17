# -*- coding: utf-8 -*-
"""
Middleware - Middlewares do auth-service
"""

from .auth_middleware import require_auth, require_admin

__all__ = ["require_auth", "require_admin"]
