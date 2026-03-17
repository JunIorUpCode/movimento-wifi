# -*- coding: utf-8 -*-
"""
Device Middleware - Middlewares de autenticação e autorização
"""

from .auth_middleware import require_auth, require_device_auth

__all__ = ["require_auth", "require_device_auth"]
