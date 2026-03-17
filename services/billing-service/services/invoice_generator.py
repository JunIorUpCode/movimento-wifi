# -*- coding: utf-8 -*-
"""
Invoice Generator - Gerador Automático de Faturas
Gera faturas mensais para todos os tenants ativos
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict
from uuid import UUID
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.invoice import Invoice, InvoiceStatus
from services.billing_service import BillingService
from services.stripe_service import StripeService
from shared.logging import get_logger

logger = get_logger(__name__)


class InvoiceGenerator:
    """
    Gerador automático de faturas mensais
    
    Executa no dia 1 de cada mês às 00:00 UTC via cron job.
    Gera faturas para todos os tenants ativos (exceto trial).
    
    Requisitos: 17.2, 17.3
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Inicializa o gerador de faturas
        
        Args:
            db_session: Sessão do banco de dados
        """
        self.db = db_session
        self.billing_service = BillingService(db_session)
        self.stripe_service = StripeService()
    
    async def generate_monthly_invoices(self) -> Dict:
        """
        Gera faturas mensais para todos os tenants ativos
        
        Deve ser executado no dia 1 de cada mês às 00:00 UTC.
        
        Returns:
            Dict com estatísticas da geração:
                - total_tenants: Total de tenants processados
                - invoices_created: Faturas criadas
                - invoices_failed: Faturas que falharam
                - total_amount: Valor total faturado
        
        Requisito: 17.2
        """
        logger.info("Iniciando geração de faturas mensais")
        
        stats = {
            "total_tenants": 0,
            "invoices_created": 0,
            "invoices_failed": 0,
            "total_amount": Decimal("0.00")
        }
        
        # Busca todos os tenants ativos (exceto trial)
        query = text("""
            SELECT id, email, name, plan_type, stripe_customer_id
            FROM tenant_schema.tenants
            WHERE status = 'active'
            ORDER BY id
        """)
        
        result = await self.db.execute(query)
        tenants = result.fetchall()
        
        stats["total_tenants"] = len(tenants)
        
        logger.info(
            f"Encontrados {len(tenants)} tenants ativos para faturamento",
            total_tenants=len(tenants)
        )
        
        # Gera fatura para cada tenant
        for tenant in tenants:
            try:
                invoice = await self._generate_invoice_for_tenant(
                    tenant_id=tenant.id,
                    tenant_email=tenant.email,
                    tenant_name=tenant.name,
                    plan_type=tenant.plan_type,
                    stripe_customer_id=tenant.stripe_customer_id
                )
                
                if invoice:
                    stats["invoices_created"] += 1
                    stats["total_amount"] += invoice.amount
                    
                    logger.info(
                        f"Fatura criada para tenant {tenant.id}: R$ {invoice.amount}",
                        tenant_id=str(tenant.id),
                        invoice_id=str(invoice.id),
                        amount=float(invoice.amount)
                    )
            
            except Exception as e:
                stats["invoices_failed"] += 1
                logger.error(
                    f"Erro ao gerar fatura para tenant {tenant.id}: {str(e)}",
                    tenant_id=str(tenant.id),
                    error=str(e)
                )
        
        logger.info(
            f"Geração de faturas concluída: {stats['invoices_created']} criadas, "
            f"{stats['invoices_failed']} falharam, total R$ {stats['total_amount']}",
            **stats
        )
        
        return stats
    
    async def _generate_invoice_for_tenant(
        self,
        tenant_id: UUID,
        tenant_email: str,
        tenant_name: str,
        plan_type: str,
        stripe_customer_id: str = None
    ) -> Invoice:
        """
        Gera uma fatura para um tenant específico
        
        Args:
            tenant_id: ID do tenant
            tenant_email: Email do tenant
            tenant_name: Nome do tenant
            plan_type: Tipo de plano
            stripe_customer_id: ID do cliente no Stripe (opcional)
        
        Returns:
            Invoice: Fatura criada
        
        Requisito: 17.2
        """
        # Calcula cobrança mensal
        charge = await self.billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type=plan_type
        )
        
        # Se não há dispositivos ativos, não gera fatura
        if charge["active_devices"] == 0:
            logger.info(
                f"Tenant {tenant_id} não possui dispositivos ativos, pulando fatura",
                tenant_id=str(tenant_id)
            )
            return None
        
        # Cria ou recupera cliente Stripe
        if not stripe_customer_id:
            stripe_customer_id = await self.stripe_service.get_or_create_customer(
                tenant_id=tenant_id,
                email=tenant_email,
                name=tenant_name
            )
            
            # Atualiza tenant com stripe_customer_id
            update_query = text("""
                UPDATE tenant_schema.tenants
                SET stripe_customer_id = :stripe_customer_id
                WHERE id = :tenant_id
            """)
            await self.db.execute(
                update_query,
                {
                    "stripe_customer_id": stripe_customer_id,
                    "tenant_id": str(tenant_id)
                }
            )
        
        # Cria fatura no banco de dados
        now = datetime.utcnow()
        due_date = now + timedelta(days=7)  # Vencimento em 7 dias
        
        invoice = Invoice(
            tenant_id=tenant_id,
            amount=charge["total"],
            status=InvoiceStatus.PENDING,
            due_date=due_date,
            line_items=charge["breakdown"],
            payment_attempts=0,
            created_at=now,
            updated_at=now
        )
        
        self.db.add(invoice)
        await self.db.flush()  # Garante que o ID seja gerado
        
        logger.info(
            f"Fatura criada no banco: {invoice.id}",
            tenant_id=str(tenant_id),
            invoice_id=str(invoice.id),
            amount=float(invoice.amount),
            due_date=due_date.isoformat()
        )
        
        return invoice
    
    async def retry_failed_payments(self) -> Dict:
        """
        Tenta novamente pagamentos que falharam
        
        Busca faturas com status FAILED e tenta cobrar novamente.
        Suspende conta após 3 tentativas falhadas.
        
        Returns:
            Dict com estatísticas do retry
        
        Requisitos: 17.4, 17.5
        """
        logger.info("Iniciando retry de pagamentos falhados")
        
        stats = {
            "total_retries": 0,
            "successful": 0,
            "failed": 0,
            "accounts_suspended": 0
        }
        
        # Busca faturas pendentes ou falhadas que precisam de retry
        # (criadas há 3 dias ou mais)
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        query = select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.FAILED]),
            Invoice.created_at <= three_days_ago,
            Invoice.payment_attempts < 3
        )
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        stats["total_retries"] = len(invoices)
        
        logger.info(
            f"Encontradas {len(invoices)} faturas para retry",
            total_retries=len(invoices)
        )
        
        for invoice in invoices:
            try:
                # Busca informações do tenant
                tenant_query = text("""
                    SELECT email, name, stripe_customer_id
                    FROM tenant_schema.tenants
                    WHERE id = :tenant_id
                """)
                tenant_result = await self.db.execute(
                    tenant_query,
                    {"tenant_id": str(invoice.tenant_id)}
                )
                tenant = tenant_result.fetchone()
                
                if not tenant or not tenant.stripe_customer_id:
                    logger.warning(
                        f"Tenant {invoice.tenant_id} não possui stripe_customer_id",
                        tenant_id=str(invoice.tenant_id)
                    )
                    continue
                
                # Tenta cobrar
                result = await self.stripe_service.charge_invoice(
                    stripe_customer_id=tenant.stripe_customer_id,
                    amount=invoice.amount,
                    invoice_id=invoice.id,
                    description=f"Fatura {invoice.id} - Tentativa {invoice.payment_attempts + 1}"
                )
                
                # Atualiza fatura
                invoice.payment_attempts += 1
                
                if result["success"]:
                    invoice.status = InvoiceStatus.PAID
                    invoice.paid_at = datetime.utcnow()
                    invoice.stripe_invoice_id = result["payment_intent_id"]
                    stats["successful"] += 1
                    
                    logger.info(
                        f"Pagamento bem-sucedido na tentativa {invoice.payment_attempts}",
                        invoice_id=str(invoice.id),
                        tenant_id=str(invoice.tenant_id)
                    )
                else:
                    invoice.status = InvoiceStatus.FAILED
                    stats["failed"] += 1
                    
                    # Suspende conta após 3 falhas
                    if invoice.payment_attempts >= 3:
                        await self._suspend_tenant_account(invoice.tenant_id)
                        stats["accounts_suspended"] += 1
                        
                        logger.warning(
                            f"Conta suspensa após 3 falhas de pagamento",
                            tenant_id=str(invoice.tenant_id),
                            invoice_id=str(invoice.id)
                        )
                
                await self.db.flush()
            
            except Exception as e:
                logger.error(
                    f"Erro ao processar retry de fatura {invoice.id}: {str(e)}",
                    invoice_id=str(invoice.id),
                    error=str(e)
                )
        
        logger.info(
            f"Retry de pagamentos concluído: {stats['successful']} sucesso, "
            f"{stats['failed']} falhas, {stats['accounts_suspended']} contas suspensas",
            **stats
        )
        
        return stats
    
    async def _suspend_tenant_account(self, tenant_id: UUID):
        """
        Suspende a conta de um tenant após falhas de pagamento
        
        Args:
            tenant_id: ID do tenant a suspender
        
        Requisito: 17.5
        """
        query = text("""
            UPDATE tenant_schema.tenants
            SET status = 'suspended'
            WHERE id = :tenant_id
        """)
        
        await self.db.execute(query, {"tenant_id": str(tenant_id)})
        
        logger.warning(
            f"Conta do tenant {tenant_id} suspensa por falha de pagamento",
            tenant_id=str(tenant_id)
        )
        
        # TODO: Enviar email de notificação ao tenant
        # Isso será implementado via integração com notification-service
