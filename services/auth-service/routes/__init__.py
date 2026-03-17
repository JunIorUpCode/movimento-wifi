# -*- coding: utf-8 -*-
"""
Routes - Endpoints da API do auth-service
"""

from .auth import router as auth_router

__all__ = ["auth_router"]
