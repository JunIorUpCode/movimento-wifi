# -*- coding: utf-8 -*-
"""
Invoice Schemas - Schemas Pydantic para Faturas e Billing
Validação de entrada/saída de dados da API
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class InvoiceResponse(BaseModel):
    """
    Schema de resposta para uma fatura individual
    Requisito: 11.6
    """
    id: UUID
    tenant_id: UUID
    amount: Decimal
    status: str
    due_date: datetime
    paid_at: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None
    line_items: List[Dict[str, Any]]
    payment_attempts: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """
    Schema de resposta para lista de faturas
    Requisito: 11.6
    """
    invoices: List[InvoiceResponse]
    total: int
    page: int
    page_size: int


class SubscriptionResponse(BaseModel):
    """
    Schema de resposta para informações de assinatura
    Requisito: 11.6
    """
    tenant_id: UUID
    plan_type: str  # "basic" ou "premium"
    status: str  # "trial", "active", "suspended", "expired"
    active_devices: int
    device_limit: int
    monthly_cost: Decimal
    next_billing_date: datetime
    trial_ends_at: Optional[datetime] = None
    payment_method_configured: bool


class UsageResponse(BaseModel):
    """
    Schema de resposta para estatísticas de uso
    Requisito: 11.6
    """
    tenant_id: UUID
    current_period_start: datetime
    current_period_end: datetime
    active_devices: int
    total_events: int
    total_notifications: int
    estimated_cost: Decimal
    breakdown: List[Dict[str, Any]]  # Detalhamento por dispositivo


class UpgradeRequest(BaseModel):
    """
    Schema de requisição para upgrade de plano
    Requisito: 5.5, 5.6
    """
    new_plan: str = Field(..., description="Novo plano (basic ou premium)")
    
    @validator("new_plan")
    def validate_plan(cls, v):
        """Valida que o plano é válido"""
        if v not in ["basic", "premium"]:
            raise ValueError("Plano deve ser 'basic' ou 'premium'")
        return v


class PaymentMethodRequest(BaseModel):
    """
    Schema de requisição para atualizar método de pagamento
    Requisito: 17.7
    """
    stripe_payment_method_id: str = Field(
        ...,
        description="ID do método de pagamento no Stripe"
    )
    set_as_default: bool = Field(
        default=True,
        description="Definir como método de pagamento padrão"
    )
