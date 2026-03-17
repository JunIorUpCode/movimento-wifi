# -*- coding: utf-8 -*-
"""
Middleware - Middlewares do Billing Service
"""

from middleware.auth_middleware import require_auth

__all__ = ["require_auth"]
