# -*- coding: utf-8 -*-
"""
License Validator - Validador de licenças online
Implementa validação periódica de licenças a cada 24 horas
"""

import asyncio
from datetime import datetime
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.license import License, LicenseStatus
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)


class LicenseValidator:
    """
    Validador de licenças online
    Executa validações periódicas a cada 24 horas
    
    Requisitos: 4.5
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o validador de licenças
        
        Args:
            db_manager: Gerenciador de banco de dados
        """
        self.db_manager = db_manager
        self.running = False
        self._task = None
        logger.info("LicenseValidator inicializado")
    
    async def validate_all_licenses(self):
        """
        Valida todas as licenças ativas
        Verifica status (revoked, expired) e status do tenant
        
        Requisitos: 4.5
        """
        logger.info("Iniciando validação de licenças...")
        
        try:
            async with self.db_manager.get_session() as session:
                # Busca todas as licenças ativadas
                result = await session.execute(
                    select(License).where(
                        License.status == LicenseStatus.ACTIVATED
                    )
                )
                licenses = list(result.scalars().all())
                
                logger.info(f"Validando {len(licenses)} licenças ativas")
                
                expired_count = 0
                
                for license in licenses:
                    # Verifica se licença expirou
                    if license.expires_at < datetime.utcnow():
                        license.status = LicenseStatus.EXPIRED
                        license.updated_at = datetime.utcnow()
                        expired_count += 1
                        
                        logger.warning(
                            "Licença expirada detectada",
                            license_id=str(license.id),
                            tenant_id=str(license.tenant_id),
                            device_id=str(license.device_id) if license.device_id else None,
                            expires_at=license.expires_at.isoformat()
                        )
                
                # Commit das alterações
                await session.commit()
                
                logger.info(
                    "Validação de licenças concluída",
                    total_validated=len(licenses),
                    expired=expired_count
                )
        
        except Exception as e:
            logger.error(
                f"Erro ao validar licenças: {str(e)}",
                error=str(e)
            )
    
    async def validate_license(
        self,
        license_id: str,
        session: AsyncSession
    ) -> bool:
        """
        Valida uma licença específica
        
        Args:
            license_id: ID da licença
            session: Sessão do banco de dados
        
        Returns:
            True se licença válida, False caso contrário
        
        Requisitos: 4.5
        """
        try:
            # Busca licença
            result = await session.execute(
                select(License).where(License.id == license_id)
            )
            license = result.scalar_one_or_none()
            
            if not license:
                logger.warning(f"Licença não encontrada: {license_id}")
                return False
            
            # Verifica status
            if license.status == LicenseStatus.REVOKED:
                logger.warning(
                    "Licença revogada",
                    license_id=license_id,
                    tenant_id=str(license.tenant_id)
                )
                return False
            
            # Verifica expiração
            if license.expires_at < datetime.utcnow():
                license.status = LicenseStatus.EXPIRED
                license.updated_at = datetime.utcnow()
                await session.flush()
                
                logger.warning(
                    "Licença expirada",
                    license_id=license_id,
                    tenant_id=str(license.tenant_id),
                    expires_at=license.expires_at.isoformat()
                )
                return False
            
            # Licença válida
            return True
        
        except Exception as e:
            logger.error(
                f"Erro ao validar licença {license_id}: {str(e)}",
                license_id=license_id,
                error=str(e)
            )
            return False
    
    async def run_periodic_validation(self):
        """
        Executa validação periódica a cada 24 horas
        Loop infinito que roda enquanto self.running for True
        
        Requisitos: 4.5
        """
        logger.info("Iniciando validação periódica de licenças (24h)")
        
        while self.running:
            try:
                # Executa validação
                await self.validate_all_licenses()
                
                # Aguarda 24 horas (86400 segundos)
                logger.info("Próxima validação em 24 horas")
                await asyncio.sleep(86400)
            
            except asyncio.CancelledError:
                logger.info("Validação periódica cancelada")
                break
            
            except Exception as e:
                logger.error(
                    f"Erro na validação periódica: {str(e)}",
                    error=str(e)
                )
                # Aguarda 1 hora antes de tentar novamente em caso de erro
                await asyncio.sleep(3600)
    
    def start(self):
        """Inicia o validador periódico"""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self.run_periodic_validation())
            logger.info("LicenseValidator iniciado")
    
    def stop(self):
        """Para o validador periódico"""
        if self.running:
            self.running = False
            if self._task:
                self._task.cancel()
            logger.info("LicenseValidator parado")


# Função factory para criar validador
def create_license_validator(db_manager: DatabaseManager) -> LicenseValidator:
    """Cria instância do validador de licenças"""
    return LicenseValidator(db_manager)
