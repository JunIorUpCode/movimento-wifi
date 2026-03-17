# -*- coding: utf-8 -*-
"""
Billing Service - Serviço de Cálculo de Cobrança
Responsável por calcular valores de cobrança mensal com descontos
"""

from decimal import Decimal
from typing import Dict, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.logging import get_logger

logger = get_logger(__name__)


class BillingService:
    """
    Serviço de cálculo de cobrança mensal
    
    Calcula valores baseados em:
    - Número de dispositivos ativos
    - Tipo de plano (BÁSICO R$ 29,90 ou PREMIUM R$ 79,90)
    - Descontos por volume (10% para 3+, 20% para 10+)
    
    Requisitos: 5.7, 17.1, 17.8
    """
    
    # Preços por plano (em reais)
    PLAN_PRICES = {
        "basic": Decimal("29.90"),
        "premium": Decimal("79.90")
    }
    
    # Descontos por volume
    VOLUME_DISCOUNTS = [
        {"min_devices": 10, "discount": Decimal("0.20")},  # 20% para 10+
        {"min_devices": 3, "discount": Decimal("0.10")},   # 10% para 3+
    ]
    
    def __init__(self, db_session: AsyncSession):
        """
        Inicializa o serviço de billing
        
        Args:
            db_session: Sessão do banco de dados
        """
        self.db = db_session
    
    async def calculate_monthly_charge(
        self,
        tenant_id: UUID,
        plan_type: str
    ) -> Dict:
        """
        Calcula a cobrança mensal para um tenant
        
        Args:
            tenant_id: ID do tenant
            plan_type: Tipo de plano ("basic" ou "premium")
        
        Returns:
            Dict com:
                - subtotal: Valor antes dos descontos
                - discount_percent: Percentual de desconto aplicado
                - discount_amount: Valor do desconto
                - total: Valor final após desconto
                - active_devices: Número de dispositivos ativos
                - breakdown: Lista com detalhamento por dispositivo
        
        Requisitos: 5.7, 17.1, 17.8
        """
        logger.info(
            f"Calculando cobrança mensal para tenant {tenant_id}",
            tenant_id=str(tenant_id),
            plan_type=plan_type
        )
        
        # Busca dispositivos ativos do tenant
        # Nota: Assumindo que existe uma tabela devices em device_schema
        # que pode ser acessada via query cross-schema
        from sqlalchemy import text
        
        query = text("""
            SELECT id, name, status
            FROM device_schema.devices
            WHERE tenant_id = :tenant_id
            AND status IN ('online', 'offline')
            AND status != 'deactivated'
        """)
        
        result = await self.db.execute(query, {"tenant_id": str(tenant_id)})
        devices = result.fetchall()
        
        active_devices = len(devices)
        
        logger.info(
            f"Tenant {tenant_id} possui {active_devices} dispositivos ativos",
            tenant_id=str(tenant_id),
            active_devices=active_devices
        )
        
        # Se não há dispositivos ativos, cobrança é zero
        if active_devices == 0:
            return {
                "subtotal": Decimal("0.00"),
                "discount_percent": Decimal("0.00"),
                "discount_amount": Decimal("0.00"),
                "total": Decimal("0.00"),
                "active_devices": 0,
                "breakdown": []
            }
        
        # Calcula subtotal (preço por dispositivo * quantidade)
        price_per_device = self.PLAN_PRICES.get(plan_type, self.PLAN_PRICES["basic"])
        subtotal = price_per_device * active_devices
        
        # Aplica desconto por volume
        discount_percent = self._get_volume_discount(active_devices)
        discount_amount = subtotal * discount_percent
        total = subtotal - discount_amount
        
        # Cria breakdown detalhado
        breakdown = []
        for device in devices:
            breakdown.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "plan": plan_type,
                "price": float(price_per_device)
            })
        
        logger.info(
            f"Cobrança calculada: subtotal={subtotal}, desconto={discount_percent*100}%, total={total}",
            tenant_id=str(tenant_id),
            subtotal=float(subtotal),
            discount_percent=float(discount_percent),
            total=float(total)
        )
        
        return {
            "subtotal": subtotal,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "total": total,
            "active_devices": active_devices,
            "breakdown": breakdown
        }
    
    def _get_volume_discount(self, device_count: int) -> Decimal:
        """
        Retorna o percentual de desconto baseado no número de dispositivos
        
        Args:
            device_count: Número de dispositivos ativos
        
        Returns:
            Decimal: Percentual de desconto (0.10 para 10%, 0.20 para 20%)
        
        Requisitos: 17.8
        """
        for discount_tier in self.VOLUME_DISCOUNTS:
            if device_count >= discount_tier["min_devices"]:
                return discount_tier["discount"]
        
        return Decimal("0.00")
    
    async def get_usage_stats(self, tenant_id: UUID) -> Dict:
        """
        Obtém estatísticas de uso do tenant no período atual
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Dict com estatísticas de uso
        
        Requisito: 11.6
        """
        from datetime import datetime, timedelta
        
        # Período atual (mês corrente)
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        
        # Próximo mês
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1)
        
        # Conta eventos no período
        query_events = text("""
            SELECT COUNT(*) as total
            FROM event_schema.events
            WHERE tenant_id = :tenant_id
            AND timestamp >= :period_start
            AND timestamp < :period_end
        """)
        
        result_events = await self.db.execute(
            query_events,
            {
                "tenant_id": str(tenant_id),
                "period_start": period_start,
                "period_end": period_end
            }
        )
        total_events = result_events.scalar() or 0
        
        # Conta notificações no período
        query_notifications = text("""
            SELECT COUNT(*) as total
            FROM notification_schema.notification_logs
            WHERE tenant_id = :tenant_id
            AND timestamp >= :period_start
            AND timestamp < :period_end
        """)
        
        result_notifications = await self.db.execute(
            query_notifications,
            {
                "tenant_id": str(tenant_id),
                "period_start": period_start,
                "period_end": period_end
            }
        )
        total_notifications = result_notifications.scalar() or 0
        
        logger.info(
            f"Estatísticas de uso: eventos={total_events}, notificações={total_notifications}",
            tenant_id=str(tenant_id),
            total_events=total_events,
            total_notifications=total_notifications
        )
        
        return {
            "period_start": period_start,
            "period_end": period_end,
            "total_events": total_events,
            "total_notifications": total_notifications
        }
