# -*- coding: utf-8 -*-
"""
Device Service - Serviço principal de gerenciamento de dispositivos
Implementa operações CRUD e consultas de dispositivos
"""

from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from models.device import Device, DeviceStatus
from shared.logging import get_logger

logger = get_logger(__name__)


class DeviceService:
    """
    Serviço de gerenciamento de dispositivos
    Implementa operações CRUD e consultas
    
    Requisitos: 3.5, 3.6, 13.2-13.7
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa o serviço de dispositivos
        
        Args:
            session: Sessão do banco de dados
        """
        self.session = session
    
    async def list_devices(self, tenant_id: uuid.UUID) -> List[Device]:
        """
        Lista todos os dispositivos de um tenant
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Lista de dispositivos
        
        Requisitos: 13.2
        """
        logger.info(
            f"Listando dispositivos para tenant: {tenant_id}",
            tenant_id=str(tenant_id)
        )
        
        stmt = select(Device).where(Device.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        devices = result.scalars().all()
        
        logger.info(
            f"Encontrados {len(devices)} dispositivos para tenant {tenant_id}",
            tenant_id=str(tenant_id),
            count=len(devices)
        )
        
        return list(devices)
    
    async def get_device(self, device_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Device]:
        """
        Obtém detalhes de um dispositivo específico
        
        Args:
            device_id: ID do dispositivo
            tenant_id: ID do tenant (para isolamento)
        
        Returns:
            Dispositivo ou None se não encontrado
        
        Requisitos: 13.3
        """
        logger.info(
            f"Buscando dispositivo {device_id} para tenant {tenant_id}",
            device_id=str(device_id),
            tenant_id=str(tenant_id)
        )
        
        stmt = select(Device).where(
            Device.id == device_id,
            Device.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        device = result.scalar_one_or_none()
        
        if device:
            logger.info(
                f"Dispositivo encontrado: {device.name}",
                device_id=str(device_id),
                device_name=device.name
            )
        else:
            logger.warning(
                f"Dispositivo não encontrado: {device_id}",
                device_id=str(device_id),
                tenant_id=str(tenant_id)
            )
        
        return device
    
    async def update_device(
        self,
        device_id: uuid.UUID,
        tenant_id: uuid.UUID,
        name: Optional[str] = None,
        config: Optional[dict] = None
    ) -> Optional[Device]:
        """
        Atualiza configuração de um dispositivo
        
        Args:
            device_id: ID do dispositivo
            tenant_id: ID do tenant (para isolamento)
            name: Novo nome do dispositivo (opcional)
            config: Nova configuração (opcional)
        
        Returns:
            Dispositivo atualizado ou None se não encontrado
        
        Requisitos: 13.4, 24.4-24.7
        """
        logger.info(
            f"Atualizando dispositivo {device_id}",
            device_id=str(device_id),
            tenant_id=str(tenant_id)
        )
        
        # Busca dispositivo
        device = await self.get_device(device_id, tenant_id)
        if not device:
            return None
        
        # Atualiza campos
        if name is not None:
            device.name = name
            logger.info(
                f"Nome do dispositivo atualizado para: {name}",
                device_id=str(device_id),
                new_name=name
            )
        
        if config is not None:
            # Valida configuração básica
            if not isinstance(config, dict):
                logger.error(
                    "Configuração inválida: deve ser um dicionário",
                    device_id=str(device_id)
                )
                raise ValueError("Configuração deve ser um dicionário")
            
            device.config = config
            logger.info(
                f"Configuração do dispositivo atualizada",
                device_id=str(device_id),
                config_keys=list(config.keys())
            )
        
        device.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(device)
        
        logger.info(
            f"Dispositivo atualizado com sucesso: {device_id}",
            device_id=str(device_id)
        )
        
        return device
    
    async def deactivate_device(
        self,
        device_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> bool:
        """
        Desativa um dispositivo (soft delete)
        Remove credenciais e marca como offline
        
        Args:
            device_id: ID do dispositivo
            tenant_id: ID do tenant (para isolamento)
        
        Returns:
            True se desativado com sucesso, False se não encontrado
        
        Requisitos: 3.7, 13.5
        """
        logger.info(
            f"Desativando dispositivo {device_id}",
            device_id=str(device_id),
            tenant_id=str(tenant_id)
        )
        
        # Busca dispositivo
        device = await self.get_device(device_id, tenant_id)
        if not device:
            return False
        
        # Marca como offline e remove token
        device.status = DeviceStatus.OFFLINE
        device.jwt_token_hash = None
        device.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info(
            f"Dispositivo desativado com sucesso: {device_id}",
            device_id=str(device_id)
        )
        
        return True
    
    async def get_device_status(
        self,
        device_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> Optional[dict]:
        """
        Obtém status em tempo real de um dispositivo
        
        Args:
            device_id: ID do dispositivo
            tenant_id: ID do tenant (para isolamento)
        
        Returns:
            Dicionário com status ou None se não encontrado
        
        Requisitos: 13.6
        """
        device = await self.get_device(device_id, tenant_id)
        if not device:
            return None
        
        # Calcula tempo desde último heartbeat
        time_since_last_seen = (datetime.utcnow() - device.last_seen).total_seconds()
        
        return {
            "device_id": str(device.id),
            "name": device.name,
            "status": device.status.value,
            "last_seen": device.last_seen.isoformat(),
            "seconds_since_last_seen": int(time_since_last_seen),
            "hardware_type": device.hardware_type.value,
            "hardware_info": device.hardware_info
        }
