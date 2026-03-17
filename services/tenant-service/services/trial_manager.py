# -*- coding: utf-8 -*-
"""
Trial Manager - Gerenciamento de períodos de trial
Verifica trials expirados e envia lembretes
"""

import asyncio
from datetime import datetime
from typing import List

from services.tenant_service import tenant_service
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)


class TrialManager:
    """
    Gerenciador de períodos de trial
    
    Responsabilidades:
    - Verificar trials expirados e suspender contas
    - Enviar lembretes 3 dias e 1 dia antes do fim
    - Executar verificações periódicas
    
    Requisitos: 18.1-18.7
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o gerenciador de trials
        
        Args:
            db_manager: Gerenciador de banco de dados
        """
        self.db_manager = db_manager
        self.running = False
    
    async def check_expired_trials(self):
        """
        Verifica e suspende tenants com trial expirado
        
        Requisitos: 18.4
        """
        try:
            async with self.db_manager.get_session() as session:
                expired_tenants = await tenant_service.check_expired_trials(session)
                
                if expired_tenants:
                    logger.info(
                        f"Suspensos {len(expired_tenants)} tenants com trial expirado",
                        count=len(expired_tenants)
                    )
                    
                    # TODO: Enviar email notificando sobre expiração
                    # Será implementado quando notification-service estiver pronto
                    for tenant in expired_tenants:
                        logger.info(
                            f"Trial expirado: {tenant.email}",
                            tenant_id=str(tenant.id),
                            email=tenant.email
                        )
        
        except Exception as e:
            logger.error(f"Erro ao verificar trials expirados: {str(e)}", error=str(e))
    
    async def send_trial_reminders(self, days: int):
        """
        Envia lembretes para tenants cujo trial está próximo do fim
        
        Args:
            days: Número de dias antes do fim (3 ou 1)
        
        Requisitos: 18.2, 18.3
        """
        try:
            async with self.db_manager.get_session() as session:
                tenants = await tenant_service.get_tenants_trial_ending_soon(
                    session=session,
                    days=days
                )
                
                if tenants:
                    logger.info(
                        f"Encontrados {len(tenants)} tenants com trial terminando em {days} dias",
                        count=len(tenants),
                        days=days
                    )
                    
                    # TODO: Enviar emails de lembrete
                    # Será implementado quando notification-service estiver pronto
                    for tenant in tenants:
                        logger.info(
                            f"Lembrete de trial ({days} dias): {tenant.email}",
                            tenant_id=str(tenant.id),
                            email=tenant.email,
                            trial_ends_at=tenant.trial_ends_at.isoformat()
                        )
        
        except Exception as e:
            logger.error(
                f"Erro ao enviar lembretes de trial ({days} dias): {str(e)}",
                error=str(e),
                days=days
            )
    
    async def run_periodic_checks(self):
        """
        Executa verificações periódicas de trials
        
        - Verifica trials expirados a cada 1 hora
        - Envia lembretes de 3 dias a cada 6 horas
        - Envia lembretes de 1 dia a cada 6 horas
        """
        logger.info("Iniciando verificações periódicas de trials")
        self.running = True
        
        # Contadores para controlar frequência
        hour_counter = 0
        
        while self.running:
            try:
                # Verifica trials expirados a cada hora
                await self.check_expired_trials()
                
                # Envia lembretes a cada 6 horas
                if hour_counter % 6 == 0:
                    await self.send_trial_reminders(days=3)
                    await self.send_trial_reminders(days=1)
                
                hour_counter += 1
                
                # Aguarda 1 hora
                await asyncio.sleep(3600)
            
            except Exception as e:
                logger.error(f"Erro nas verificações periódicas: {str(e)}", error=str(e))
                # Aguarda 5 minutos antes de tentar novamente
                await asyncio.sleep(300)
    
    def stop(self):
        """Para as verificações periódicas"""
        logger.info("Parando verificações periódicas de trials")
        self.running = False
