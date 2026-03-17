# -*- coding: utf-8 -*-
"""
Cliente HTTP para comunicação com Backend Central
Implementa retry com exponential backoff e compressão de dados
"""

import aiohttp
import asyncio
import gzip
import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class HTTPClient:
    """
    Cliente HTTP para comunicação com o backend central.
    Implementa retry com exponential backoff e compressão gzip.
    """
    
    def __init__(
        self,
        backend_url: str,
        jwt_token: Optional[str] = None,
        retry_max_attempts: int = 3,
        retry_backoff_base: float = 2.0,
        retry_initial_delay: float = 1.0,
        timeout: int = 30
    ):
        """
        Inicializa o cliente HTTP.
        
        Args:
            backend_url: URL base do backend (ex: https://api.wifisense.com)
            jwt_token: Token JWT para autenticação
            retry_max_attempts: Número máximo de tentativas em caso de falha
            retry_backoff_base: Base para exponential backoff
            retry_initial_delay: Delay inicial em segundos
            timeout: Timeout para requisições em segundos
        """
        self.backend_url = backend_url.rstrip('/')
        self.jwt_token = jwt_token
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff_base = retry_backoff_base
        self.retry_initial_delay = retry_initial_delay
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Retorna ou cria sessão HTTP"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def close(self) -> None:
        """Fecha a sessão HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_headers(self, compress: bool = False) -> Dict[str, str]:
        """
        Retorna headers HTTP com autenticação.
        
        Args:
            compress: Se True, adiciona Content-Encoding: gzip
        
        Returns:
            Dict com headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "WiFiSense-Agent/1.0"
        }
        
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        if compress:
            headers["Content-Encoding"] = "gzip"
        
        return headers
    
    def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """
        Comprime dados usando gzip.
        
        Args:
            data: Dados a comprimir
        
        Returns:
            bytes: Dados comprimidos
        """
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return gzip.compress(json_data)
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        compress: bool = False
    ) -> Dict[str, Any]:
        """
        Faz requisição HTTP com retry e exponential backoff.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (ex: /api/devices/register)
            data: Dados a enviar (para POST/PUT)
            compress: Se True, comprime dados com gzip
        
        Returns:
            Dict com resposta JSON
        
        Raises:
            aiohttp.ClientError: Se todas as tentativas falharem
        """
        url = f"{self.backend_url}{endpoint}"
        session = await self._get_session()
        
        for attempt in range(self.retry_max_attempts):
            try:
                # Prepara dados
                if data and compress:
                    body = self._compress_data(data)
                    headers = self._get_headers(compress=True)
                elif data:
                    body = json.dumps(data, ensure_ascii=False)
                    headers = self._get_headers(compress=False)
                else:
                    body = None
                    headers = self._get_headers(compress=False)
                
                # Faz requisição
                async with session.request(
                    method,
                    url,
                    data=body,
                    headers=headers
                ) as response:
                    # Verifica status
                    if response.status >= 500:
                        # Erro do servidor, tenta novamente
                        raise aiohttp.ClientError(f"Server error: {response.status}")
                    
                    # Lê resposta
                    response_data = await response.json()
                    
                    # Verifica se foi sucesso
                    if response.status >= 400:
                        # Erro do cliente, não tenta novamente
                        raise aiohttp.ClientError(
                            f"Client error {response.status}: {response_data}"
                        )
                    
                    return response_data
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Se é a última tentativa, propaga o erro
                if attempt == self.retry_max_attempts - 1:
                    print(f"[HTTPClient] Falha após {self.retry_max_attempts} tentativas: {e}")
                    raise
                
                # Calcula delay com exponential backoff
                delay = self.retry_initial_delay * (self.retry_backoff_base ** attempt)
                print(f"[HTTPClient] Tentativa {attempt + 1} falhou, retry em {delay:.1f}s: {e}")
                
                await asyncio.sleep(delay)
        
        # Nunca deve chegar aqui
        raise aiohttp.ClientError("Retry loop failed unexpectedly")
    
    async def register_device(
        self,
        activation_key: str,
        hardware_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra dispositivo com o backend.
        
        Args:
            activation_key: Chave de ativação fornecida pelo usuário
            hardware_info: Informações do hardware (type, os, csi_capable, etc)
        
        Returns:
            Dict com device_id, jwt_token e config
        
        Raises:
            aiohttp.ClientError: Se registro falhar
        """
        return await self._request_with_retry(
            "POST",
            "/api/devices/register",
            data={
                "activation_key": activation_key,
                "hardware_info": hardware_info
            }
        )
    
    async def send_heartbeat(
        self,
        device_id: str,
        health_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia heartbeat para o backend.
        
        Args:
            device_id: ID do dispositivo
            health_metrics: Métricas de saúde (cpu_percent, memory_mb, disk_percent)
        
        Returns:
            Dict com resposta do backend
        """
        return await self._request_with_retry(
            "POST",
            f"/api/devices/{device_id}/heartbeat",
            data=health_metrics
        )
    
    async def send_data(
        self,
        device_id: str,
        features: Dict[str, Any],
        compress: bool = True
    ) -> Dict[str, Any]:
        """
        Envia dados processados para o backend.
        
        Args:
            device_id: ID do dispositivo
            features: Features extraídas do sinal
            compress: Se True, comprime dados com gzip
        
        Returns:
            Dict com resposta do backend
        """
        return await self._request_with_retry(
            "POST",
            f"/api/devices/{device_id}/data",
            data=features,
            compress=compress
        )
    
    async def send_batch_data(
        self,
        device_id: str,
        batch: List[Dict[str, Any]],
        compress: bool = True
    ) -> Dict[str, Any]:
        """
        Envia lote de dados (usado para upload de buffer offline).
        
        Args:
            device_id: ID do dispositivo
            batch: Lista de features com timestamps originais
            compress: Se True, comprime dados com gzip
        
        Returns:
            Dict com resposta do backend
        """
        return await self._request_with_retry(
            "POST",
            f"/api/devices/{device_id}/data/batch",
            data={"batch": batch},
            compress=compress
        )
    
    def set_jwt_token(self, token: str) -> None:
        """Atualiza o token JWT"""
        self.jwt_token = token
