# -*- coding: utf-8 -*-
"""
Middleware Package - Middlewares do license-service
"""

from middleware.auth_middleware import require_auth, require_admin

__all__ = ["require_auth", "require_admin"]
