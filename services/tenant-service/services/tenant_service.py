# -*- coding: utf-8 -*-
"""
Tenant Service - Lógica de negócio para gerenciamento de tenants
Implementa CRUD, suspensão, ativação e gerenciamento de trial
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from models.tenant import Tenant, PlanType, TenantStatus
from shared.logging import get_logger

logger = get_logger(__name__)


class TenantService:
    """
    Serviço de gerenciamento de tenants
    
    Responsabilidades:
    - CRUD de tenants
    - Suspensão e ativação de contas
    - Gerenciamento de período de trial
    - Validação de dados
    
    Requisitos: 2.1-2.6, 18.1-18.7
    """
    
    async def create_tenant(
        self,
        email: str,
        name: str,
        plan_type: PlanType,
        session: AsyncSession
    ) -> Tenant:
        """
        Cria um novo tenant com período de trial de 7 dias
        
        Args:
            email: Email do tenant (único)
            name: Nome do tenant
            plan_type: Tipo de plano (BASIC ou PREMIUM)
            session: Sessão do banco de dados
        
        Returns:
            Tenant criado
        
        Raises:
            ValueError: Se email já existe
        
        Requisitos: 2.2, 18.1
        """
        # Verifica se email já existe
        result = await session.execute(
            select(Tenant).where(Tenant.email == email)
        )
        existing_tenant = result.scalar_one_or_none()
        
        if existing_tenant:
            logger.warning(f"Tentativa de criar tenant com email duplicado: {email}")
            raise ValueError(f"Email {email} já está em uso")
        
        # Cria tenant com trial de 7 dias
        trial_ends_at = datetime.utcnow() + timedelta(days=7)
        
        tenant = Tenant(
            email=email,
            name=name,
            plan_type=plan_type,
            status=TenantStatus.TRIAL,
            trial_ends_at=trial_ends_at
        )
        
        session.add(tenant)
        await session.flush()
        
        logger.info(
            f"Tenant criado com sucesso: {email}",
            tenant_id=str(tenant.id),
            email=email,
            plan=plan_type.value,
            trial_ends_at=trial_ends_at.isoformat()
        )
        
        return tenant
    
    async def get_tenant_by_id(
        self,
        tenant_id: UUID,
        session: AsyncSession
    ) -> Optional[Tenant]:
        """
        Busca tenant por ID
        
        Args:
            tenant_id: ID do tenant
            session: Sessão do banco de dados
        
        Returns:
            Tenant encontrado ou None
        
        Requisitos: 2.3
        """
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tenant_by_email(
        self,
        email: str,
        session: AsyncSession
    ) -> Optional[Tenant]:
        """
        Busca tenant por email
        
        Args:
            email: Email do tenant
            session: Sessão do banco de dados
        
        Returns:
            Tenant encontrado ou None
        """
        result = await session.execute(
            select(Tenant).where(Tenant.email == email)
        )
        return result.scalar_one_or_none()
    
    async def list_tenants(
        self,
        session: AsyncSession,
        status: Optional[TenantStatus] = None,
        plan_type: Optional[PlanType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """
        Lista tenants com filtros opcionais
        
        Args:
            session: Sessão do banco de dados
            status: Filtrar por status (opcional)
            plan_type: Filtrar por tipo de plano (opcional)
            limit: Limite de resultados
            offset: Offset para paginação
        
        Returns:
            Lista de tenants
        
        Requisitos: 2.3
        """
        query = select(Tenant)
        
        # Aplica filtros
        if status:
            query = query.where(Tenant.status == status)
        if plan_type:
            query = query.where(Tenant.plan_type == plan_type)
        
        # Ordena por data de criação (mais recentes primeiro)
        query = query.order_by(Tenant.created_at.desc())
        
        # Aplica paginação
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def count_tenants(
        self,
        session: AsyncSession,
        status: Optional[TenantStatus] = None,
        plan_type: Optional[PlanType] = None
    ) -> int:
        """
        Conta total de tenants com filtros opcionais
        
        Args:
            session: Sessão do banco de dados
            status: Filtrar por status (opcional)
            plan_type: Filtrar por tipo de plano (opcional)
        
        Returns:
            Total de tenants
        """
        query = select(func.count(Tenant.id))
        
        if status:
            query = query.where(Tenant.status == status)
        if plan_type:
            query = query.where(Tenant.plan_type == plan_type)
        
        result = await session.execute(query)
        return result.scalar_one()
    
    async def update_tenant(
        self,
        tenant_id: UUID,
        session: AsyncSession,
        name: Optional[str] = None,
        plan_type: Optional[PlanType] = None,
        language: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[Tenant]:
        """
        Atualiza informações do tenant
        
        Args:
            tenant_id: ID do tenant
            session: Sessão do banco de dados
            name: Novo nome (opcional)
            plan_type: Novo tipo de plano (opcional)
            language: Novo idioma (opcional)
            metadata: Novos metadados (opcional)
        
        Returns:
            Tenant atualizado ou None se não encontrado
        
        Requisitos: 2.3
        """
        tenant = await self.get_tenant_by_id(tenant_id, session)
        
        if not tenant:
            logger.warning(f"Tentativa de atualizar tenant inexistente: {tenant_id}")
            return None
        
        # Atualiza campos fornecidos
        if name is not None:
            tenant.name = name
        if plan_type is not None:
            tenant.plan_type = plan_type
        if language is not None:
            tenant.language = language
        if metadata is not None:
            tenant.extra_metadata = metadata
        
        tenant.updated_at = datetime.utcnow()
        
        await session.flush()
        
        logger.info(
            f"Tenant atualizado: {tenant.email}",
            tenant_id=str(tenant_id),
            email=tenant.email
        )
        
        return tenant
    
    async def suspend_tenant(
        self,
        tenant_id: UUID,
        session: AsyncSession
    ) -> Optional[Tenant]:
        """
        Suspende um tenant
        
        - Altera status para SUSPENDED
        - Bloqueia acesso a APIs
        
        Args:
            tenant_id: ID do tenant
            session: Sessão do banco de dados
        
        Returns:
            Tenant suspenso ou None se não encontrado
        
        Requisitos: 2.4, 2.5
        """
        tenant = await self.get_tenant_by_id(tenant_id, session)
        
        if not tenant:
            logger.warning(f"Tentativa de suspender tenant inexistente: {tenant_id}")
            return None
        
        tenant.status = TenantStatus.SUSPENDED
        tenant.updated_at = datetime.utcnow()
        
        await session.flush()
        
        logger.warning(
            f"Tenant suspenso: {tenant.email}",
            tenant_id=str(tenant_id),
            email=tenant.email
        )
        
        return tenant
    
    async def activate_tenant(
        self,
        tenant_id: UUID,
        session: AsyncSession
    ) -> Optional[Tenant]:
        """
        Ativa um tenant suspenso
        
        - Altera status para ACTIVE
        - Restaura acesso a APIs
        
        Args:
            tenant_id: ID do tenant
            session: Sessão do banco de dados
        
        Returns:
            Tenant ativado ou None se não encontrado
        
        Requisitos: 2.4
        """
        tenant = await self.get_tenant_by_id(tenant_id, session)
        
        if not tenant:
            logger.warning(f"Tentativa de ativar tenant inexistente: {tenant_id}")
            return None
        
        tenant.status = TenantStatus.ACTIVE
        tenant.updated_at = datetime.utcnow()
        
        await session.flush()
        
        logger.info(
            f"Tenant ativado: {tenant.email}",
            tenant_id=str(tenant_id),
            email=tenant.email
        )
        
        return tenant
    
    async def delete_tenant(
        self,
        tenant_id: UUID,
        session: AsyncSession
    ) -> bool:
        """
        Deleta um tenant (cascade)
        
        ATENÇÃO: Esta operação é irreversível e deve deletar
        todos os dados relacionados (dispositivos, eventos, etc.)
        
        Args:
            tenant_id: ID do tenant
            session: Sessão do banco de dados
        
        Returns:
            True se deletado, False se não encontrado
        
        Requisitos: 2.6
        """
        tenant = await self.get_tenant_by_id(tenant_id, session)
        
        if not tenant:
            logger.warning(f"Tentativa de deletar tenant inexistente: {tenant_id}")
            return False
        
        await session.delete(tenant)
        await session.flush()
        
        logger.critical(
            f"Tenant deletado: {tenant.email}",
            tenant_id=str(tenant_id),
            email=tenant.email
        )
        
        return True
    
    async def check_expired_trials(
        self,
        session: AsyncSession
    ) -> List[Tenant]:
        """
        Verifica e suspende tenants com trial expirado
        
        - Busca tenants em TRIAL com trial_ends_at < now()
        - Altera status para EXPIRED
        
        Returns:
            Lista de tenants com trial expirado
        
        Requisitos: 18.4
        """
        now = datetime.utcnow()
        
        # Busca tenants com trial expirado
        result = await session.execute(
            select(Tenant).where(
                Tenant.status == TenantStatus.TRIAL,
                Tenant.trial_ends_at < now
            )
        )
        expired_tenants = list(result.scalars().all())
        
        # Suspende cada tenant
        for tenant in expired_tenants:
            tenant.status = TenantStatus.EXPIRED
            tenant.updated_at = now
            
            logger.warning(
                f"Trial expirado para tenant: {tenant.email}",
                tenant_id=str(tenant.id),
                email=tenant.email,
                trial_ends_at=tenant.trial_ends_at.isoformat()
            )
        
        if expired_tenants:
            await session.flush()
        
        return expired_tenants
    
    async def get_tenants_trial_ending_soon(
        self,
        session: AsyncSession,
        days: int = 3
    ) -> List[Tenant]:
        """
        Busca tenants cujo trial está próximo do fim
        
        Args:
            session: Sessão do banco de dados
            days: Número de dias antes do fim (padrão: 3)
        
        Returns:
            Lista de tenants com trial terminando em N dias
        
        Requisitos: 18.2, 18.3
        """
        now = datetime.utcnow()
        target_date = now + timedelta(days=days)
        
        # Busca tenants em trial que expiram em aproximadamente N dias
        # (com margem de 1 hora para evitar múltiplos envios)
        result = await session.execute(
            select(Tenant).where(
                Tenant.status == TenantStatus.TRIAL,
                Tenant.trial_ends_at >= target_date - timedelta(hours=1),
                Tenant.trial_ends_at <= target_date + timedelta(hours=1)
            )
        )
        
        return list(result.scalars().all())


# Instância global do serviço
tenant_service = TenantService()
