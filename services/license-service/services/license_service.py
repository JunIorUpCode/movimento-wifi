# -*- coding: utf-8 -*-
"""
License Service - Serviço de gerenciamento de licenças
Implementa lógica de negócio para criação, validação e revogação de licenças
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.license import License, LicenseStatus, PlanType
from services.license_generator import license_generator
from shared.logging import get_logger

logger = get_logger(__name__)


class LicenseService:
    """
    Serviço para gerenciar licenças
    Implementa CRUD e validação de licenças
    """
    
    async def create_license(
        self,
        tenant_id: UUID,
        plan_type: PlanType,
        device_limit: int,
        expires_in_days: int,
        session: AsyncSession
    ) -> License:
        """
        Cria uma nova licença para um tenant
        
        Args:
            tenant_id: ID do tenant proprietário
            plan_type: Tipo de plano (basic ou premium)
            device_limit: Limite de dispositivos
            expires_in_days: Dias até expiração
            session: Sessão do banco de dados
        
        Returns:
            Licença criada
        
        Requisitos: 4.1, 4.2
        """
        # Gera chave de ativação
        activation_key, key_hash = license_generator.generate_activation_key()
        
        # Calcula data de expiração
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Cria licença
        license = License(
            tenant_id=tenant_id,
            activation_key=activation_key,
            activation_key_hash=key_hash,
            plan_type=plan_type,
            device_limit=device_limit,
            expires_at=expires_at,
            status=LicenseStatus.PENDING
        )
        
        session.add(license)
        await session.flush()
        
        logger.info(
            "Licença criada com sucesso",
            license_id=str(license.id),
            tenant_id=str(tenant_id),
            plan_type=plan_type.value,
            device_limit=device_limit,
            expires_at=expires_at.isoformat()
        )
        
        return license
    
    async def get_license_by_id(
        self,
        license_id: UUID,
        session: AsyncSession
    ) -> Optional[License]:
        """
        Busca licença por ID
        
        Args:
            license_id: ID da licença
            session: Sessão do banco de dados
        
        Returns:
            Licença encontrada ou None
        """
        result = await session.execute(
            select(License).where(License.id == license_id)
        )
        return result.scalar_one_or_none()
    
    async def get_license_by_key(
        self,
        activation_key: str,
        session: AsyncSession
    ) -> Optional[License]:
        """
        Busca licença por chave de ativação
        
        Args:
            activation_key: Chave de ativação
            session: Sessão do banco de dados
        
        Returns:
            Licença encontrada ou None
        """
        # Normaliza chave
        normalized_key = license_generator.normalize_key(activation_key)
        
        result = await session.execute(
            select(License).where(License.activation_key == normalized_key)
        )
        return result.scalar_one_or_none()
    
    async def list_licenses(
        self,
        session: AsyncSession,
        tenant_id: Optional[UUID] = None,
        status: Optional[LicenseStatus] = None,
        plan_type: Optional[PlanType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[License]:
        """
        Lista licenças com filtros opcionais
        
        Args:
            session: Sessão do banco de dados
            tenant_id: Filtrar por tenant
            status: Filtrar por status
            plan_type: Filtrar por tipo de plano
            limit: Limite de resultados
            offset: Offset para paginação
        
        Returns:
            Lista de licenças
        
        Requisitos: 4.1
        """
        query = select(License)
        
        # Aplica filtros
        if tenant_id:
            query = query.where(License.tenant_id == tenant_id)
        if status:
            query = query.where(License.status == status)
        if plan_type:
            query = query.where(License.plan_type == plan_type)
        
        # Ordena por data de criação (mais recentes primeiro)
        query = query.order_by(License.created_at.desc())
        
        # Aplica paginação
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def count_licenses(
        self,
        session: AsyncSession,
        tenant_id: Optional[UUID] = None,
        status: Optional[LicenseStatus] = None,
        plan_type: Optional[PlanType] = None
    ) -> int:
        """
        Conta licenças com filtros opcionais
        
        Args:
            session: Sessão do banco de dados
            tenant_id: Filtrar por tenant
            status: Filtrar por status
            plan_type: Filtrar por tipo de plano
        
        Returns:
            Número de licenças
        """
        query = select(func.count(License.id))
        
        # Aplica filtros
        if tenant_id:
            query = query.where(License.tenant_id == tenant_id)
        if status:
            query = query.where(License.status == status)
        if plan_type:
            query = query.where(License.plan_type == plan_type)
        
        result = await session.execute(query)
        return result.scalar_one()
    
    async def revoke_license(
        self,
        license_id: UUID,
        session: AsyncSession
    ) -> Optional[License]:
        """
        Revoga uma licença
        
        Args:
            license_id: ID da licença
            session: Sessão do banco de dados
        
        Returns:
            Licença revogada ou None se não encontrada
        
        Requisitos: 4.7
        """
        license = await self.get_license_by_id(license_id, session)
        
        if not license:
            return None
        
        license.status = LicenseStatus.REVOKED
        license.updated_at = datetime.utcnow()
        
        await session.flush()
        
        logger.info(
            "Licença revogada",
            license_id=str(license_id),
            tenant_id=str(license.tenant_id)
        )
        
        return license
    
    async def extend_license(
        self,
        license_id: UUID,
        additional_days: int,
        session: AsyncSession
    ) -> Optional[License]:
        """
        Estende a expiração de uma licença
        
        Args:
            license_id: ID da licença
            additional_days: Dias adicionais
            session: Sessão do banco de dados
        
        Returns:
            Licença atualizada ou None se não encontrada
        
        Requisitos: 4.7
        """
        license = await self.get_license_by_id(license_id, session)
        
        if not license:
            return None
        
        # Estende expiração
        license.expires_at = license.expires_at + timedelta(days=additional_days)
        license.updated_at = datetime.utcnow()
        
        # Se estava expirada, reativa
        if license.status == LicenseStatus.EXPIRED:
            license.status = LicenseStatus.ACTIVATED if license.activated_at else LicenseStatus.PENDING
        
        await session.flush()
        
        logger.info(
            "Licença estendida",
            license_id=str(license_id),
            additional_days=additional_days,
            new_expires_at=license.expires_at.isoformat()
        )
        
        return license
    
    async def activate_license(
        self,
        activation_key: str,
        device_id: UUID,
        session: AsyncSession
    ) -> License:
        """
        Ativa uma licença com um dispositivo
        
        Args:
            activation_key: Chave de ativação
            device_id: ID do dispositivo
            session: Sessão do banco de dados
        
        Returns:
            Licença ativada
        
        Raises:
            ValueError: Se licença inválida, expirada ou já ativada
        
        Requisitos: 4.4
        """
        # Busca licença
        license = await self.get_license_by_key(activation_key, session)
        
        if not license:
            raise ValueError("Chave de ativação inválida")
        
        # Verifica status
        if license.status == LicenseStatus.REVOKED:
            raise ValueError("Licença revogada")
        
        if license.status == LicenseStatus.EXPIRED:
            raise ValueError("Licença expirada")
        
        if license.status == LicenseStatus.ACTIVATED:
            raise ValueError("Licença já ativada")
        
        # Verifica expiração
        now = datetime.utcnow()
        expires_at = license.expires_at
        # Remove timezone info se presente para comparação
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        
        if expires_at < now:
            license.status = LicenseStatus.EXPIRED
            await session.flush()
            raise ValueError("Licença expirada")
        
        # Ativa licença
        license.status = LicenseStatus.ACTIVATED
        license.device_id = device_id
        license.activated_at = datetime.utcnow()
        license.updated_at = datetime.utcnow()
        
        await session.flush()
        
        logger.info(
            "Licença ativada com sucesso",
            license_id=str(license.id),
            device_id=str(device_id),
            tenant_id=str(license.tenant_id)
        )
        
        return license


# Instância global do serviço de licenças
license_service = LicenseService()
