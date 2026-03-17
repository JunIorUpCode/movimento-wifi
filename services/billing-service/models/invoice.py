# -*- coding: utf-8 -*-
"""
Invoice Model - Modelo de Fatura
Representa faturas geradas mensalmente para tenants
"""

from sqlalchemy import Column, String, Numeric, DateTime, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from shared.database import Base


class InvoiceStatus(str, enum.Enum):
    """Status possíveis de uma fatura"""
    PENDING = "pending"      # Aguardando pagamento
    PAID = "paid"           # Paga com sucesso
    FAILED = "failed"       # Falha no pagamento
    REFUNDED = "refunded"   # Reembolsada


class Invoice(Base):
    """
    Modelo de Fatura
    
    Representa uma fatura mensal gerada para um tenant.
    Inclui informações de valor, status, datas e integração com Stripe.
    
    Requisitos: 17.1, 17.2, 37.6
    """
    
    __tablename__ = "invoices"
    __table_args__ = (
        # Índice para buscar faturas por tenant (multi-tenancy)
        Index("idx_invoices_tenant_id", "tenant_id"),
        # Índice para buscar faturas por status
        Index("idx_invoices_status", "status"),
        # Índice composto para buscar faturas de um tenant por data
        Index("idx_invoices_tenant_created", "tenant_id", "created_at"),
        {"schema": "billing_schema"}
    )
    
    # Identificador único da fatura
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ID do tenant (isolamento multi-tenant)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Valor total da fatura em reais (Decimal para precisão monetária)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Status da fatura (pending, paid, failed, refunded)
    status = Column(
        Enum(InvoiceStatus, name="invoice_status_enum", schema="billing_schema"),
        nullable=False,
        default=InvoiceStatus.PENDING
    )
    
    # Data de vencimento da fatura
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    # Data em que a fatura foi paga (null se ainda não paga)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # ID da fatura no Stripe (para rastreamento)
    stripe_invoice_id = Column(String(255), nullable=True)
    
    # Itens da fatura (JSON com detalhes de cada cobrança)
    # Exemplo: [{"device_id": "...", "plan": "premium", "amount": 79.90}]
    line_items = Column(JSON, nullable=False, default=list)
    
    # Número de tentativas de pagamento falhadas
    payment_attempts = Column(Numeric(2, 0), nullable=False, default=0)
    
    # Data de criação da fatura
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Data da última atualização
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount}, status={self.status})>"
