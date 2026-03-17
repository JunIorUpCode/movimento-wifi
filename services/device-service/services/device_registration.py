# -*- coding: utf-8 -*-
"""
Device Registration - Serviço de registro de dispositivos
Implementa validação de activation_key e registro de novos dispositivos
"""

import hashlib
import uuid
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import jwt

from models.device import Device, DeviceStatus, HardwareType
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class DeviceRegistration:
    """
    Serviço de registro de dispositivos
    Valida activation_key via license-service e registra dispositivos
    
    Requisitos: 3.2, 3.3, 4.4
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa o serviço de registro
        
        Args:
            session: Sessão do banco de dados
        """
        self.session = session
        self.license_service_url = "http://license-service:8004"
    
    async def validate_activation_key(self, activation_key: str) -> dict:
        """
        Valida activation_key via license-service
        
        Args:
            activation_key: Chave de ativação fornecida pelo dispositivo
        
        Returns:
            Dicionário com informações da licença
        
        Raises:
            ValueError: Se chave inválida ou expirada
        
        Requisitos: 3.2, 4.4
        """
        logger.info(
            f"Validando activation_key: {activation_key[:4]}****",
            activation_key_prefix=activation_key[:4]
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.license_service_url}/api/licenses/validate",
                    json={"activation_key": activation_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    license_data = response.json()
                    logger.info(
                        f"Activation_key válida para tenant: {license_data.get('tenant_id')}",
                        tenant_id=license_data.get('tenant_id'),
                        plan_type=license_data.get('plan_type')
                    )
                    return license_data
                elif response.status_code == 404:
                    logger.warning(
                        f"Activation_key não encontrada ou já ativada",
                        activation_key_prefix=activation_key[:4]
                    )
                    raise ValueError("Chave de ativação inválida ou já utilizada")
                elif response.status_code == 403:
                    logger.warning(
                        f"Activation_key expirada",
                        activation_key_prefix=activation_key[:4]
                    )
                    raise ValueError("Chave de ativação expirada")
                else:
                    logger.error(
                        f"Erro ao validar activation_key: {response.status_code}",
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    raise ValueError(f"Erro ao validar chave: {response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(
                f"Erro de conexão com license-service: {str(e)}",
                error=str(e)
            )
            raise ValueError("Erro ao conectar com serviço de licenças")
    
    async def check_device_limit(self, tenant_id: uuid.UUID, device_limit: int) -> bool:
        """
        Verifica se o tenant atingiu o limite de dispositivos
        
        Args:
            tenant_id: ID do tenant
            device_limit: Limite de dispositivos da licença
        
        Returns:
            True se pode registrar mais dispositivos, False caso contrário
        
        Requisitos: 4.8
        """
        from sqlalchemy import select, func
        
        logger.info(
            f"Verificando limite de dispositivos para tenant: {tenant_id}",
            tenant_id=str(tenant_id),
            device_limit=device_limit
        )
        
        # Conta dispositivos ativos do tenant
        stmt = select(func.count(Device.id)).where(
            Device.tenant_id == tenant_id,
            Device.status != DeviceStatus.OFFLINE  # Não conta dispositivos desativados
        )
        result = await self.session.execute(stmt)
        active_devices = result.scalar()
        
        logger.info(
            f"Tenant {tenant_id} tem {active_devices} dispositivos ativos (limite: {device_limit})",
            tenant_id=str(tenant_id),
            active_devices=active_devices,
            device_limit=device_limit
        )
        
        return active_devices < device_limit
    
    def generate_device_jwt(self, device_id: uuid.UUID, tenant_id: uuid.UUID, plan_type: str = "basic") -> str:
        """
        Gera JWT token para o dispositivo
        
        Args:
            device_id: ID do dispositivo
            tenant_id: ID do tenant
            plan_type: Tipo de plano (basic ou premium)
        
        Returns:
            JWT token
        
        Requisitos: 3.3
        """
        payload = {
            "sub": str(device_id),
            "tenant_id": str(tenant_id),
            "plan_type": plan_type,
            "type": "device",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.info(
            f"JWT token gerado para dispositivo: {device_id}",
            device_id=str(device_id),
            tenant_id=str(tenant_id)
        )
        
        return token
    
    def hash_token(self, token: str) -> str:
        """
        Gera hash SHA256 do token para armazenamento
        
        Args:
            token: JWT token
        
        Returns:
            Hash SHA256 do token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def mark_license_activated(
        self,
        activation_key: str,
        device_id: uuid.UUID
    ) -> bool:
        """
        Marca licença como ativada no license-service
        
        Args:
            activation_key: Chave de ativação
            device_id: ID do dispositivo que ativou
        
        Returns:
            True se marcado com sucesso
        
        Requisitos: 4.4
        """
        logger.info(
            f"Marcando licença como ativada para dispositivo: {device_id}",
            device_id=str(device_id)
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.license_service_url}/api/licenses/activate",
                    json={
                        "activation_key": activation_key,
                        "device_id": str(device_id)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(
                        f"Licença marcada como ativada com sucesso",
                        device_id=str(device_id)
                    )
                    return True
                else:
                    logger.error(
                        f"Erro ao marcar licença como ativada: {response.status_code}",
                        status_code=response.status_code,
                        device_id=str(device_id)
                    )
                    return False
        
        except httpx.RequestError as e:
            logger.error(
                f"Erro de conexão ao marcar licença: {str(e)}",
                error=str(e),
                device_id=str(device_id)
            )
            return False
    
    async def register_device(
        self,
        activation_key: str,
        hardware_info: dict,
        device_name: Optional[str] = None
    ) -> dict:
        """
        Registra um novo dispositivo
        
        Args:
            activation_key: Chave de ativação
            hardware_info: Informações do hardware
            device_name: Nome do dispositivo (opcional)
        
        Returns:
            Dicionário com device_id, jwt_token e config
        
        Raises:
            ValueError: Se validação falhar
        
        Requisitos: 3.2, 3.3, 4.4
        """
        logger.info(
            f"Iniciando registro de dispositivo",
            activation_key_prefix=activation_key[:4],
            hardware_type=hardware_info.get("type")
        )
        
        # 1. Valida activation_key
        license_data = await self.validate_activation_key(activation_key)
        tenant_id = uuid.UUID(license_data["tenant_id"])
        plan_type = license_data["plan_type"]
        device_limit = license_data["device_limit"]
        
        # 2. Verifica limite de dispositivos
        can_register = await self.check_device_limit(tenant_id, device_limit)
        if not can_register:
            logger.warning(
                f"Limite de dispositivos atingido para tenant: {tenant_id}",
                tenant_id=str(tenant_id),
                device_limit=device_limit
            )
            raise ValueError(f"Limite de dispositivos atingido ({device_limit})")
        
        # 3. Valida hardware vs plano
        hardware_validation = self.validate_hardware_vs_plan(hardware_info, plan_type)
        
        # 4. Cria dispositivo
        device_id = uuid.uuid4()
        jwt_token = self.generate_device_jwt(device_id, tenant_id, plan_type)
        token_hash = self.hash_token(jwt_token)
        
        # Determina tipo de hardware
        hardware_type_str = hardware_info.get("type", "linux").lower()
        if "raspberry" in hardware_type_str or "rpi" in hardware_type_str:
            hardware_type = HardwareType.RASPBERRY_PI
        elif "windows" in hardware_type_str:
            hardware_type = HardwareType.WINDOWS
        else:
            hardware_type = HardwareType.LINUX
        
        # Nome padrão se não fornecido
        if not device_name:
            device_name = f"Dispositivo {hardware_type.value}"
        
        device = Device(
            id=device_id,
            tenant_id=tenant_id,
            name=device_name,
            hardware_type=hardware_type,
            status=DeviceStatus.ONLINE,
            last_seen=datetime.utcnow(),
            registered_at=datetime.utcnow(),
            hardware_info=hardware_info,
            config={
                "sampling_interval": 1,
                "detection_thresholds": {
                    "presence": 0.7,
                    "movement": 0.7,
                    "fall": 0.8
                }
            },
            jwt_token_hash=token_hash
        )
        
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        
        logger.info(
            f"Dispositivo registrado com sucesso: {device_id}",
            device_id=str(device_id),
            tenant_id=str(tenant_id),
            hardware_type=hardware_type.value
        )
        
        # 5. Marca licença como ativada
        await self.mark_license_activated(activation_key, device_id)
        
        return {
            "device_id": str(device_id),
            "jwt_token": jwt_token,
            "config": device.config,
            "hardware_validation": hardware_validation
        }
    
    def validate_hardware_vs_plan(self, hardware_info: dict, plan_type: str) -> dict:
        """
        Valida capacidades de hardware vs plano subscrito
        
        Args:
            hardware_info: Informações do hardware
            plan_type: Tipo de plano (basic ou premium)
        
        Returns:
            Dicionário com validação e sugestões
        
        Requisitos: 5.2, 5.3, 27.1-27.8
        """
        csi_capable = hardware_info.get("csi_capable", False)
        
        validation = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        # BÁSICO com hardware CSI - sugerir upgrade
        if plan_type == "basic" and csi_capable:
            validation["suggestions"].append(
                "Seu hardware suporta CSI! Considere fazer upgrade para o plano PREMIUM "
                "para detecção de quedas e análise avançada."
            )
            logger.info(
                "Hardware CSI detectado em plano BÁSICO - sugerindo upgrade",
                plan_type=plan_type,
                csi_capable=csi_capable
            )
        
        # PREMIUM sem hardware CSI - alertar
        if plan_type == "premium" and not csi_capable:
            validation["warnings"].append(
                "Seu plano PREMIUM requer hardware com suporte a CSI para recursos avançados. "
                "Hardware atual não suporta CSI - funcionalidades limitadas a RSSI."
            )
            logger.warning(
                "Plano PREMIUM sem hardware CSI - funcionalidades limitadas",
                plan_type=plan_type,
                csi_capable=csi_capable
            )
        
        return validation
