# -*- coding: utf-8 -*-
"""
Billing Routes - Endpoints de Billing e Pagamentos
Fornece endpoints para gerenciar assinaturas, faturas e pagamentos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from schemas.invoice import (
    InvoiceResponse,
    InvoiceListResponse,
    SubscriptionResponse,
    UsageResponse,
    UpgradeRequest,
    PaymentMethodRequest
)
from models.invoice import Invoice
from services.billing_service import BillingService
from services.stripe_service import StripeService
from shared.database import get_billing_db
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Dependência para obter sessão do banco
db_manager = get_billing_db()


async def get_db():
    """Dependência para obter sessão do banco de dados"""
    async with db_manager.get_session() as session:
        yield session


async def get_current_tenant_id() -> UUID:
    """
    Dependência para obter tenant_id do token JWT
    
    TODO: Implementar validação real do JWT
    Por enquanto, retorna um UUID fixo para testes
    """
    # Em produção, isso virá do middleware de autenticação
    # que decodifica o JWT e extrai o tenant_id
    return UUID("00000000-0000-0000-0000-000000000001")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém informações da assinatura atual do tenant
    
    Retorna:
        - Tipo de plano
        - Status da conta
        - Número de dispositivos ativos
        - Custo mensal
        - Próxima data de cobrança
    
    Requisito: 11.6
    """
    logger.info(
        f"Buscando assinatura para tenant {tenant_id}",
        tenant_id=str(tenant_id)
    )
    
    try:
        # Busca informações do tenant
        from sqlalchemy import text
        
        tenant_query = text("""
            SELECT id, plan_type, status, trial_ends_at
            FROM tenant_schema.tenants
            WHERE id = :tenant_id
        """)
        
        result = await db.execute(tenant_query, {"tenant_id": str(tenant_id)})
        tenant = result.fetchone()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant não encontrado"
            )
        
        # Calcula cobrança mensal
        billing_service = BillingService(db)
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type=tenant.plan_type
        )
        
        # Busca próxima fatura
        next_invoice_query = select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.status == "pending"
        ).order_by(desc(Invoice.due_date)).limit(1)
        
        next_invoice_result = await db.execute(next_invoice_query)
        next_invoice = next_invoice_result.scalar_one_or_none()
        
        # Calcula próxima data de cobrança
        if next_invoice:
            next_billing_date = next_invoice.due_date
        else:
            # Próximo dia 1 do mês
            now = datetime.utcnow()
            if now.month == 12:
                next_billing_date = datetime(now.year + 1, 1, 1)
            else:
                next_billing_date = datetime(now.year, now.month + 1, 1)
        
        # Verifica se tem método de pagamento configurado
        # TODO: Implementar verificação real no Stripe
        payment_method_configured = False
        
        return SubscriptionResponse(
            tenant_id=tenant_id,
            plan_type=tenant.plan_type,
            status=tenant.status,
            active_devices=charge["active_devices"],
            device_limit=100,  # TODO: Buscar do plano
            monthly_cost=charge["total"],
            next_billing_date=next_billing_date,
            trial_ends_at=tenant.trial_ends_at,
            payment_method_configured=payment_method_configured
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao buscar assinatura: {str(e)}",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar assinatura"
        )


@router.post("/upgrade")
async def upgrade_plan(
    request: UpgradeRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Faz upgrade do plano do tenant
    
    Atualiza o plano de BÁSICO para PREMIUM.
    O upgrade é aplicado imediatamente.
    
    Requisitos: 5.5, 5.6
    """
    logger.info(
        f"Upgrade de plano solicitado para tenant {tenant_id}: {request.new_plan}",
        tenant_id=str(tenant_id),
        new_plan=request.new_plan
    )
    
    try:
        from sqlalchemy import text
        
        # Atualiza plano do tenant
        update_query = text("""
            UPDATE tenant_schema.tenants
            SET plan_type = :new_plan,
                updated_at = NOW()
            WHERE id = :tenant_id
            RETURNING plan_type
        """)
        
        result = await db.execute(
            update_query,
            {"new_plan": request.new_plan, "tenant_id": str(tenant_id)}
        )
        
        updated = result.fetchone()
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant não encontrado"
            )
        
        await db.commit()
        
        logger.info(
            f"Plano atualizado com sucesso para {request.new_plan}",
            tenant_id=str(tenant_id),
            new_plan=request.new_plan
        )
        
        return {
            "success": True,
            "message": f"Plano atualizado para {request.new_plan}",
            "new_plan": request.new_plan
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao fazer upgrade de plano: {str(e)}",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao fazer upgrade de plano"
        )


@router.post("/payment-method")
async def update_payment_method(
    request: PaymentMethodRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza o método de pagamento do tenant
    
    Anexa um novo método de pagamento ao cliente no Stripe.
    
    Requisito: 17.7
    """
    logger.info(
        f"Atualização de método de pagamento para tenant {tenant_id}",
        tenant_id=str(tenant_id)
    )
    
    try:
        from sqlalchemy import text
        
        # Busca stripe_customer_id do tenant
        tenant_query = text("""
            SELECT stripe_customer_id, email, name
            FROM tenant_schema.tenants
            WHERE id = :tenant_id
        """)
        
        result = await db.execute(tenant_query, {"tenant_id": str(tenant_id)})
        tenant = result.fetchone()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant não encontrado"
            )
        
        # Cria ou recupera cliente Stripe
        stripe_service = StripeService()
        
        if not tenant.stripe_customer_id:
            stripe_customer_id = await stripe_service.get_or_create_customer(
                tenant_id=tenant_id,
                email=tenant.email,
                name=tenant.name
            )
            
            # Atualiza tenant com stripe_customer_id
            update_query = text("""
                UPDATE tenant_schema.tenants
                SET stripe_customer_id = :stripe_customer_id
                WHERE id = :tenant_id
            """)
            await db.execute(
                update_query,
                {
                    "stripe_customer_id": stripe_customer_id,
                    "tenant_id": str(tenant_id)
                }
            )
            await db.commit()
        else:
            stripe_customer_id = tenant.stripe_customer_id
        
        # Anexa método de pagamento
        success = await stripe_service.attach_payment_method(
            stripe_customer_id=stripe_customer_id,
            payment_method_id=request.stripe_payment_method_id,
            set_as_default=request.set_as_default
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao anexar método de pagamento"
            )
        
        logger.info(
            f"Método de pagamento atualizado com sucesso",
            tenant_id=str(tenant_id)
        )
        
        return {
            "success": True,
            "message": "Método de pagamento atualizado com sucesso"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao atualizar método de pagamento: {str(e)}",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar método de pagamento"
        )


@router.get("/invoices", response_model=InvoiceListResponse)
async def get_invoices(
    page: int = 1,
    page_size: int = 20,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista faturas do tenant com paginação
    
    Requisito: 11.6
    """
    logger.info(
        f"Listando faturas para tenant {tenant_id}",
        tenant_id=str(tenant_id),
        page=page,
        page_size=page_size
    )
    
    try:
        # Conta total de faturas
        from sqlalchemy import func
        
        count_query = select(func.count(Invoice.id)).where(
            Invoice.tenant_id == tenant_id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Busca faturas com paginação
        offset = (page - 1) * page_size
        
        invoices_query = select(Invoice).where(
            Invoice.tenant_id == tenant_id
        ).order_by(desc(Invoice.created_at)).offset(offset).limit(page_size)
        
        invoices_result = await db.execute(invoices_query)
        invoices = invoices_result.scalars().all()
        
        return InvoiceListResponse(
            invoices=[InvoiceResponse.from_orm(inv) for inv in invoices],
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(
            f"Erro ao listar faturas: {str(e)}",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar faturas"
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém estatísticas de uso do tenant no período atual
    
    Requisito: 11.6
    """
    logger.info(
        f"Buscando estatísticas de uso para tenant {tenant_id}",
        tenant_id=str(tenant_id)
    )
    
    try:
        billing_service = BillingService(db)
        
        # Busca informações do tenant
        from sqlalchemy import text
        
        tenant_query = text("""
            SELECT plan_type
            FROM tenant_schema.tenants
            WHERE id = :tenant_id
        """)
        
        result = await db.execute(tenant_query, {"tenant_id": str(tenant_id)})
        tenant = result.fetchone()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant não encontrado"
            )
        
        # Calcula cobrança estimada
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type=tenant.plan_type
        )
        
        # Busca estatísticas de uso
        usage_stats = await billing_service.get_usage_stats(tenant_id)
        
        return UsageResponse(
            tenant_id=tenant_id,
            current_period_start=usage_stats["period_start"],
            current_period_end=usage_stats["period_end"],
            active_devices=charge["active_devices"],
            total_events=usage_stats["total_events"],
            total_notifications=usage_stats["total_notifications"],
            estimated_cost=charge["total"],
            breakdown=charge["breakdown"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao buscar estatísticas de uso: {str(e)}",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar estatísticas de uso"
        )
