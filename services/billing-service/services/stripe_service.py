# -*- coding: utf-8 -*-
"""
Stripe Service - Integração com Stripe para Pagamentos
Gerencia clientes, métodos de pagamento e cobranças via Stripe
"""

from typing import Optional, Dict
from uuid import UUID
from decimal import Decimal
import stripe
from datetime import datetime

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class StripeService:
    """
    Serviço de integração com Stripe
    
    Responsável por:
    - Criar/recuperar clientes Stripe
    - Processar pagamentos
    - Gerenciar métodos de pagamento
    - Criar faturas no Stripe
    
    Requisitos: 17.3, 17.4
    """
    
    def __init__(self):
        """
        Inicializa o serviço Stripe com API key
        """
        # Configura API key do Stripe
        stripe.api_key = settings.STRIPE_API_KEY
        logger.info("StripeService inicializado")
    
    async def get_or_create_customer(
        self,
        tenant_id: UUID,
        email: str,
        name: str
    ) -> str:
        """
        Obtém ou cria um cliente no Stripe
        
        Args:
            tenant_id: ID do tenant
            email: Email do tenant
            name: Nome do tenant
        
        Returns:
            str: ID do cliente no Stripe (stripe_customer_id)
        
        Requisito: 17.3
        """
        try:
            # Busca cliente existente por metadata
            customers = stripe.Customer.list(
                email=email,
                limit=1
            )
            
            if customers.data:
                customer = customers.data[0]
                logger.info(
                    f"Cliente Stripe encontrado: {customer.id}",
                    tenant_id=str(tenant_id),
                    stripe_customer_id=customer.id
                )
                return customer.id
            
            # Cria novo cliente
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "tenant_id": str(tenant_id)
                }
            )
            
            logger.info(
                f"Cliente Stripe criado: {customer.id}",
                tenant_id=str(tenant_id),
                stripe_customer_id=customer.id
            )
            
            return customer.id
        
        except stripe.error.StripeError as e:
            logger.error(
                f"Erro ao criar/buscar cliente Stripe: {str(e)}",
                tenant_id=str(tenant_id),
                error=str(e)
            )
            raise
    
    async def create_payment_intent(
        self,
        stripe_customer_id: str,
        amount: Decimal,
        invoice_id: UUID,
        description: str
    ) -> Dict:
        """
        Cria um PaymentIntent no Stripe para cobrar uma fatura
        
        Args:
            stripe_customer_id: ID do cliente no Stripe
            amount: Valor a cobrar (em reais)
            invoice_id: ID da fatura
            description: Descrição do pagamento
        
        Returns:
            Dict com informações do PaymentIntent
        
        Requisito: 17.3
        """
        try:
            # Converte reais para centavos (Stripe usa centavos)
            amount_cents = int(amount * 100)
            
            # Cria PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="brl",
                customer=stripe_customer_id,
                description=description,
                metadata={
                    "invoice_id": str(invoice_id)
                },
                automatic_payment_methods={
                    "enabled": True
                }
            )
            
            logger.info(
                f"PaymentIntent criado: {payment_intent.id}",
                invoice_id=str(invoice_id),
                payment_intent_id=payment_intent.id,
                amount=float(amount)
            )
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "status": payment_intent.status
            }
        
        except stripe.error.StripeError as e:
            logger.error(
                f"Erro ao criar PaymentIntent: {str(e)}",
                invoice_id=str(invoice_id),
                error=str(e)
            )
            raise
    
    async def charge_invoice(
        self,
        stripe_customer_id: str,
        amount: Decimal,
        invoice_id: UUID,
        description: str
    ) -> Dict:
        """
        Cobra uma fatura usando o método de pagamento padrão do cliente
        
        Args:
            stripe_customer_id: ID do cliente no Stripe
            amount: Valor a cobrar
            invoice_id: ID da fatura
            description: Descrição da cobrança
        
        Returns:
            Dict com resultado da cobrança (success, payment_intent_id, error)
        
        Requisito: 17.3
        """
        try:
            # Cria e confirma PaymentIntent automaticamente
            payment_intent = await self.create_payment_intent(
                stripe_customer_id=stripe_customer_id,
                amount=amount,
                invoice_id=invoice_id,
                description=description
            )
            
            # Confirma o pagamento
            confirmed = stripe.PaymentIntent.confirm(
                payment_intent["payment_intent_id"]
            )
            
            success = confirmed.status == "succeeded"
            
            logger.info(
                f"Cobrança processada: status={confirmed.status}",
                invoice_id=str(invoice_id),
                payment_intent_id=confirmed.id,
                success=success
            )
            
            return {
                "success": success,
                "payment_intent_id": confirmed.id,
                "status": confirmed.status,
                "error": None
            }
        
        except stripe.error.CardError as e:
            # Erro de cartão (recusado, sem fundos, etc)
            logger.warning(
                f"Cartão recusado: {e.user_message}",
                invoice_id=str(invoice_id),
                error=e.user_message
            )
            return {
                "success": False,
                "payment_intent_id": None,
                "status": "failed",
                "error": e.user_message
            }
        
        except stripe.error.StripeError as e:
            # Outros erros do Stripe
            logger.error(
                f"Erro ao processar pagamento: {str(e)}",
                invoice_id=str(invoice_id),
                error=str(e)
            )
            return {
                "success": False,
                "payment_intent_id": None,
                "status": "error",
                "error": str(e)
            }
    
    async def attach_payment_method(
        self,
        stripe_customer_id: str,
        payment_method_id: str,
        set_as_default: bool = True
    ) -> bool:
        """
        Anexa um método de pagamento a um cliente
        
        Args:
            stripe_customer_id: ID do cliente no Stripe
            payment_method_id: ID do método de pagamento
            set_as_default: Se deve definir como padrão
        
        Returns:
            bool: True se sucesso, False caso contrário
        
        Requisito: 17.7
        """
        try:
            # Anexa método de pagamento ao cliente
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer_id
            )
            
            # Define como padrão se solicitado
            if set_as_default:
                stripe.Customer.modify(
                    stripe_customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method_id
                    }
                )
            
            logger.info(
                f"Método de pagamento anexado: {payment_method_id}",
                stripe_customer_id=stripe_customer_id,
                payment_method_id=payment_method_id,
                set_as_default=set_as_default
            )
            
            return True
        
        except stripe.error.StripeError as e:
            logger.error(
                f"Erro ao anexar método de pagamento: {str(e)}",
                stripe_customer_id=stripe_customer_id,
                error=str(e)
            )
            return False
    
    async def get_payment_methods(self, stripe_customer_id: str) -> list:
        """
        Lista métodos de pagamento de um cliente
        
        Args:
            stripe_customer_id: ID do cliente no Stripe
        
        Returns:
            list: Lista de métodos de pagamento
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id,
                type="card"
            )
            
            return payment_methods.data
        
        except stripe.error.StripeError as e:
            logger.error(
                f"Erro ao listar métodos de pagamento: {str(e)}",
                stripe_customer_id=stripe_customer_id,
                error=str(e)
            )
            return []
