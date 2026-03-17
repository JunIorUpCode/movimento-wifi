# -*- coding: utf-8 -*-
"""
Device Heartbeat - Serviço de heartbeat de dispositivos
Implementa recepção de heartbeat e detecção de dispositivos offline
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from models.device import Device, DeviceStatus
from shared.logging import get_logger

logger = get_logger(__name__)


class DeviceHeartbeat:
    """
    Serviço de heartbeat de dispositivos
    Recebe heartbeats e detecta dispositivos offline
    
    Requisitos: 39.1-39.3
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa o serviço de heartbeat
        
        Args:
            session: Sessão do banco de dados
        """
        self.session = session
        self.heartbeat_timeout = 180  # 3 minutos (3 heartbeats perdidos)
    
    async def process_heartbeat(
        self,
        device_id: uuid.UUID,
        tenant_id: uuid.UUID,
        health_metrics: Optional[dict] = None
    ) -> dict:
        """
        Processa heartbeat de um dispositivo
        
        Args:
            device_id: ID do dispositivo
            tenant_id: ID do tenant (para isolamento)
            health_metrics: Métricas de saúde (CPU, memória, disco)
        
        Returns:
            Dicionário com status do heartbeat
        
        Raises:
            ValueError: Se dispositivo não encontrado
        
        Requisitos: 39.1, 39.6
        """
        logger.debug(
            f"Processando heartbeat para dispositivo: {device_id}",
            device_id=str(device_id),
            tenant_id=str(tenant_id)
        )
        
        # Busca dispositivo
        stmt = select(Device).where(
            Device.id == device_id,
            Device.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            logger.warning(
                f"Dispositivo não encontrado para heartbeat: {device_id}",
                device_id=str(device_id),
                tenant_id=str(tenant_id)
            )
            raise ValueError("Dispositivo não encontrado")
        
        # Atualiza last_seen e status
        device.last_seen = datetime.utcnow()
        device.status = DeviceStatus.ONLINE
        device.updated_at = datetime.utcnow()
        
        # Armazena métricas de saúde se fornecidas
        if health_metrics:
            # Valida métricas
            if not isinstance(health_metrics, dict):
                logger.warning(
                    f"Métricas de saúde inválidas para dispositivo: {device_id}",
                    device_id=str(device_id)
                )
            else:
                # Atualiza hardware_info com métricas
                device.hardware_info["last_health_metrics"] = {
                    "cpu_percent": health_metrics.get("cpu_percent"),
                    "memory_mb": health_metrics.get("memory_mb"),
                    "disk_percent": health_metrics.get("disk_percent"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.debug(
                    f"Métricas de saúde atualizadas para dispositivo: {device_id}",
                    device_id=str(device_id),
                    cpu=health_metrics.get("cpu_percent"),
                    memory=health_metrics.get("memory_mb"),
                    disk=health_metrics.get("disk_percent")
                )
        
        await self.session.commit()
        
        logger.debug(
            f"Heartbeat processado com sucesso para dispositivo: {device_id}",
            device_id=str(device_id)
        )
        
        return {
            "status": "ok",
            "device_id": str(device_id),
            "last_seen": device.last_seen.isoformat(),
            "device_status": device.status.value
        }
    
    async def check_offline_devices(self) -> int:
        """
        Verifica dispositivos que não enviaram heartbeat há mais de 3 minutos
        Marca como offline automaticamente
        
        Returns:
            Número de dispositivos marcados como offline
        
        Requisitos: 39.2, 39.3
        """
        logger.info("Verificando dispositivos offline...")
        
        # Calcula timestamp de timeout (3 minutos atrás)
        timeout_threshold = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
        
        # Busca dispositivos online que não enviaram heartbeat
        stmt = select(Device).where(
            Device.status == DeviceStatus.ONLINE,
            Device.last_seen < timeout_threshold
        )
        result = await self.session.execute(stmt)
        offline_devices = result.scalars().all()
        
        if not offline_devices:
            logger.info("Nenhum dispositivo offline detectado")
            return 0
        
        # Marca como offline
        count = 0
        for device in offline_devices:
            device.status = DeviceStatus.OFFLINE
            device.updated_at = datetime.utcnow()
            count += 1
            
            logger.warning(
                f"Dispositivo marcado como offline: {device.id} ({device.name})",
                device_id=str(device.id),
                device_name=device.name,
                tenant_id=str(device.tenant_id),
                last_seen=device.last_seen.isoformat()
            )
        
        await self.session.commit()
        
        logger.info(
            f"{count} dispositivos marcados como offline",
            count=count
        )
        
        return count


class OfflineDetectionWorker:
    """
    Worker que executa verificação periódica de dispositivos offline
    Roda em background a cada 60 segundos
    
    Requisitos: 39.2, 39.3
    """
    
    def __init__(self, db_manager):
        """
        Inicializa o worker
        
        Args:
            db_manager: DatabaseManager para criar sessões
        """
        self.db_manager = db_manager
        self.running = False
        self.task = None
    
    async def run(self):
        """
        Loop principal do worker
        Executa verificação a cada 60 segundos
        """
        logger.info("OfflineDetectionWorker iniciado")
        self.running = True
        
        while self.running:
            try:
                # Cria sessão para verificação
                async with self.db_manager.get_session() as session:
                    heartbeat_service = DeviceHeartbeat(session)
                    count = await heartbeat_service.check_offline_devices()
                    
                    if count > 0:
                        logger.info(
                            f"Verificação de offline concluída: {count} dispositivos marcados",
                            count=count
                        )
                
                # Aguarda 60 segundos antes da próxima verificação
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(
                    f"Erro no OfflineDetectionWorker: {str(e)}",
                    error=str(e)
                )
                # Aguarda antes de tentar novamente
                await asyncio.sleep(60)
    
    def start(self):
        """Inicia o worker em background"""
        if not self.running:
            self.task = asyncio.create_task(self.run())
            logger.info("OfflineDetectionWorker task criada")
    
    def stop(self):
        """Para o worker"""
        logger.info("Parando OfflineDetectionWorker...")
        self.running = False
        if self.task:
            self.task.cancel()
