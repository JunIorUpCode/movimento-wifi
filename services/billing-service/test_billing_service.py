# -*- coding: utf-8 -*-
"""
Testes Unitários - Billing Service
Testa cálculo de cobrança, descontos e geração de faturas

Requisitos testados: 5.7, 17.1, 17.2, 17.8
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Adiciona o diretório do serviço ao path
sys.path.insert(0, str(Path(__file__).parent))

from services.billing_service import BillingService
from services.invoice_generator import InvoiceGenerator
from models.invoice import Invoice, InvoiceStatus


class TestBillingService:
    """Testes para BillingService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock da sessão do banco de dados"""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def billing_service(self, mock_db_session):
        """Instância do BillingService para testes"""
        return BillingService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_charge_basic_plan_1_device(self, billing_service, mock_db_session):
        """
        Testa cálculo de cobrança para plano BÁSICO com 1 dispositivo
        
        Esperado:
        - Subtotal: R$ 29,90
        - Desconto: 0%
        - Total: R$ 29,90
        
        Requisito: 5.7, 17.1
        """
        tenant_id = uuid4()
        
        # Mock do resultado da query de dispositivos
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(id=uuid4(), name="Device 1", status="online")
        ]
        mock_db_session.execute.return_value = mock_result
        
        # Calcula cobrança
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type="basic"
        )
        
        # Verifica resultados
        assert charge["active_devices"] == 1
        assert charge["subtotal"] == Decimal("29.90")
        assert charge["discount_percent"] == Decimal("0.00")
        assert charge["discount_amount"] == Decimal("0.00")
        assert charge["total"] == Decimal("29.90")
        assert len(charge["breakdown"]) == 1
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_charge_premium_plan_1_device(self, billing_service, mock_db_session):
        """
        Testa cálculo de cobrança para plano PREMIUM com 1 dispositivo
        
        Esperado:
        - Subtotal: R$ 79,90
        - Desconto: 0%
        - Total: R$ 79,90
        
        Requisito: 5.7, 17.1
        """
        tenant_id = uuid4()
        
        # Mock do resultado da query
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(id=uuid4(), name="Device 1", status="online")
        ]
        mock_db_session.execute.return_value = mock_result
        
        # Calcula cobrança
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type="premium"
        )
        
        # Verifica resultados
        assert charge["active_devices"] == 1
        assert charge["subtotal"] == Decimal("79.90")
        assert charge["discount_percent"] == Decimal("0.00")
        assert charge["total"] == Decimal("79.90")
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_charge_3_devices_10_percent_discount(self, billing_service, mock_db_session):
        """
        Testa cálculo com 3 dispositivos (desconto de 10%)
        
        Esperado:
        - Subtotal: R$ 89,70 (3 x 29,90)
        - Desconto: 10% = R$ 8,97
        - Total: R$ 80,73
        
        Requisito: 17.8
        """
        tenant_id = uuid4()
        
        # Mock com 3 dispositivos
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(id=uuid4(), name=f"Device {i}", status="online")
            for i in range(1, 4)
        ]
        mock_db_session.execute.return_value = mock_result
        
        # Calcula cobrança
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type="basic"
        )
        
        # Verifica resultados
        assert charge["active_devices"] == 3
        assert charge["subtotal"] == Decimal("89.70")  # 3 x 29.90
        assert charge["discount_percent"] == Decimal("0.10")  # 10%
        assert charge["discount_amount"] == Decimal("8.97")
        assert charge["total"] == Decimal("80.73")
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_charge_10_devices_20_percent_discount(self, billing_service, mock_db_session):
        """
        Testa cálculo com 10 dispositivos (desconto de 20%)
        
        Esperado:
        - Subtotal: R$ 299,00 (10 x 29,90)
        - Desconto: 20% = R$ 59,80
        - Total: R$ 239,20
        
        Requisito: 17.8
        """
        tenant_id = uuid4()
        
        # Mock com 10 dispositivos
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(id=uuid4(), name=f"Device {i}", status="online")
            for i in range(1, 11)
        ]
        mock_db_session.execute.return_value = mock_result
        
        # Calcula cobrança
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type="basic"
        )
        
        # Verifica resultados
        assert charge["active_devices"] == 10
        assert charge["subtotal"] == Decimal("299.00")  # 10 x 29.90
        assert charge["discount_percent"] == Decimal("0.20")  # 20%
        assert charge["discount_amount"] == Decimal("59.80")
        assert charge["total"] == Decimal("239.20")
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_charge_no_devices(self, billing_service, mock_db_session):
        """
        Testa cálculo quando não há dispositivos ativos
        
        Esperado:
        - Total: R$ 0,00
        
        Requisito: 17.1
        """
        tenant_id = uuid4()
        
        # Mock sem dispositivos
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        # Calcula cobrança
        charge = await billing_service.calculate_monthly_charge(
            tenant_id=tenant_id,
            plan_type="basic"
        )
        
        # Verifica resultados
        assert charge["active_devices"] == 0
        assert charge["total"] == Decimal("0.00")
        assert charge["breakdown"] == []
    
    def test_get_volume_discount_no_discount(self, billing_service):
        """
        Testa desconto por volume com menos de 3 dispositivos
        
        Esperado: 0% de desconto
        
        Requisito: 17.8
        """
        assert billing_service._get_volume_discount(1) == Decimal("0.00")
        assert billing_service._get_volume_discount(2) == Decimal("0.00")
    
    def test_get_volume_discount_10_percent(self, billing_service):
        """
        Testa desconto por volume com 3-9 dispositivos
        
        Esperado: 10% de desconto
        
        Requisito: 17.8
        """
        assert billing_service._get_volume_discount(3) == Decimal("0.10")
        assert billing_service._get_volume_discount(5) == Decimal("0.10")
        assert billing_service._get_volume_discount(9) == Decimal("0.10")
    
    def test_get_volume_discount_20_percent(self, billing_service):
        """
        Testa desconto por volume com 10+ dispositivos
        
        Esperado: 20% de desconto
        
        Requisito: 17.8
        """
        assert billing_service._get_volume_discount(10) == Decimal("0.20")
        assert billing_service._get_volume_discount(15) == Decimal("0.20")
        assert billing_service._get_volume_discount(100) == Decimal("0.20")


class TestInvoiceGenerator:
    """Testes para InvoiceGenerator"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock da sessão do banco de dados"""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def invoice_generator(self, mock_db_session):
        """Instância do InvoiceGenerator para testes"""
        # Mock do StripeService para evitar inicialização real
        with patch('services.invoice_generator.StripeService'):
            return InvoiceGenerator(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_generate_invoice_for_tenant_with_devices(self, mock_db_session):
        """
        Testa geração de fatura para tenant com dispositivos ativos
        
        Requisito: 17.2
        """
        tenant_id = uuid4()
        
        # Mock do StripeService
        with patch('services.invoice_generator.StripeService') as MockStripeService:
            # Cria instância mockada
            mock_stripe = AsyncMock()
            mock_stripe.get_or_create_customer = AsyncMock(return_value="cus_test123")
            MockStripeService.return_value = mock_stripe
            
            # Cria invoice generator
            invoice_generator = InvoiceGenerator(mock_db_session)
            invoice_generator.stripe_service = mock_stripe
            
            # Mock do cálculo de cobrança
            with patch.object(
                invoice_generator.billing_service,
                'calculate_monthly_charge',
                return_value={
                    "active_devices": 2,
                    "total": Decimal("59.80"),
                    "breakdown": [
                        {"device_id": str(uuid4()), "plan": "basic", "price": 29.90},
                        {"device_id": str(uuid4()), "plan": "basic", "price": 29.90}
                    ]
                }
            ):
                # Gera fatura
                invoice = await invoice_generator._generate_invoice_for_tenant(
                    tenant_id=tenant_id,
                    tenant_email="test@example.com",
                    tenant_name="Test Tenant",
                    plan_type="basic",
                    stripe_customer_id=None
                )
                
                # Verifica fatura criada
                assert invoice is not None
                assert invoice.tenant_id == tenant_id
                assert invoice.amount == Decimal("59.80")
                assert invoice.status == InvoiceStatus.PENDING
                assert len(invoice.line_items) == 2
                assert invoice.payment_attempts == 0
    
    @pytest.mark.asyncio
    async def test_generate_invoice_for_tenant_without_devices(self, mock_db_session):
        """
        Testa que não gera fatura para tenant sem dispositivos
        
        Requisito: 17.2
        """
        tenant_id = uuid4()
        
        # Mock do StripeService
        with patch('services.invoice_generator.StripeService') as MockStripeService:
            mock_stripe = AsyncMock()
            MockStripeService.return_value = mock_stripe
            
            # Cria invoice generator
            invoice_generator = InvoiceGenerator(mock_db_session)
            invoice_generator.stripe_service = mock_stripe
            
            # Mock do cálculo de cobrança sem dispositivos
            with patch.object(
                invoice_generator.billing_service,
                'calculate_monthly_charge',
                return_value={
                    "active_devices": 0,
                    "total": Decimal("0.00"),
                    "breakdown": []
                }
            ):
                # Tenta gerar fatura
                invoice = await invoice_generator._generate_invoice_for_tenant(
                    tenant_id=tenant_id,
                    tenant_email="test@example.com",
                    tenant_name="Test Tenant",
                    plan_type="basic",
                    stripe_customer_id=None
                )
                
                # Verifica que não criou fatura
                assert invoice is None


class TestStripeIntegration:
    """Testes de integração com Stripe (mocked)"""
    
    @pytest.mark.asyncio
    async def test_stripe_payment_success(self):
        """
        Testa pagamento bem-sucedido via Stripe
        
        Requisito: 17.3
        """
        # Mock do Stripe antes de importar StripeService
        with patch('stripe.api_key', 'sk_test_mock'):
            from services.stripe_service import StripeService
            
            stripe_service = StripeService()
        # Mock do Stripe
        with patch('stripe.PaymentIntent.create') as mock_create:
            with patch('stripe.PaymentIntent.confirm') as mock_confirm:
                # Configura mocks
                mock_create.return_value = MagicMock(
                    id="pi_test123",
                    client_secret="secret_test",
                    status="requires_confirmation"
                )
                mock_confirm.return_value = MagicMock(
                    id="pi_test123",
                    status="succeeded"
                )
                
                # Tenta cobrar fatura
                result = await stripe_service.charge_invoice(
                    stripe_customer_id="cus_test123",
                    amount=Decimal("29.90"),
                    invoice_id=uuid4(),
                    description="Test invoice"
                )
                
                # Verifica sucesso
                assert result["success"] is True
                assert result["status"] == "succeeded"
                assert result["payment_intent_id"] == "pi_test123"
    
    @pytest.mark.asyncio
    async def test_stripe_payment_card_declined(self):
        """
        Testa pagamento recusado (cartão sem fundos)
        
        Requisito: 17.4
        """
        import stripe
        
        # Mock do Stripe antes de importar StripeService
        with patch('stripe.api_key', 'sk_test_mock'):
            from services.stripe_service import StripeService
            
            stripe_service = StripeService()
        
        # Mock do Stripe com erro de cartão
        with patch('stripe.PaymentIntent.create') as mock_create:
            with patch('stripe.PaymentIntent.confirm') as mock_confirm:
                # Simula erro de cartão
                mock_confirm.side_effect = stripe.error.CardError(
                    message="Your card was declined",
                    param="card",
                    code="card_declined"
                )
                
                mock_create.return_value = MagicMock(
                    id="pi_test123",
                    client_secret="secret_test",
                    status="requires_confirmation"
                )
                
                # Tenta cobrar fatura
                result = await stripe_service.charge_invoice(
                    stripe_customer_id="cus_test123",
                    amount=Decimal("29.90"),
                    invoice_id=uuid4(),
                    description="Test invoice"
                )
                
                # Verifica falha
                assert result["success"] is False
                assert result["status"] == "failed"
                assert result["error"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
