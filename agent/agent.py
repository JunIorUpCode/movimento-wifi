# -*- coding: utf-8 -*-
"""
Agente Local WiFiSense
Coordena captura, processamento, transmissão e buffer de dados
"""

import asyncio
import psutil
from typing import Optional, Dict, Any
from datetime import datetime

from agent.config import ConfigManager, AgentConfig
from agent.capture import CaptureManager
from agent.processing import FeatureExtractor
from agent.storage import BufferManager
from agent.api_client import HTTPClient, WebSocketClient
from agent.hardware_detector import HardwareDetector


class WiFiSenseAgent:
    """
    Agente local WiFiSense.
    Coordena todos os módulos: captura, processamento, transmissão e buffer.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Inicializa o agente.
        
        Args:
            config_dir: Diretório para configurações (se None, usa ~/.wifisense_agent/)
        """
        # Gerenciadores
        self.config_manager = ConfigManager(config_dir)
        self.config: AgentConfig = self.config_manager.load_config()
        
        # Módulos
        self.capture_manager: Optional[CaptureManager] = None
        self.feature_extractor: Optional[FeatureExtractor] = None
        self.buffer_manager: Optional[BufferManager] = None
        self.http_client: Optional[HTTPClient] = None
        self.ws_client: Optional[WebSocketClient] = None
        
        # Estado
        self._running = False
        self._online = False
        self._capture_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._upload_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Inicia o agente"""
        print("\n" + "="*60)
        print("WiFiSense Agent - Iniciando")
        print("="*60)
        
        # Verifica se está ativado
        if not self.config_manager.is_activated():
            print("\n[Agent] Dispositivo não ativado!")
            await self._activate_device()
        
        # Inicializa módulos
        await self._init_modules()
        
        # Inicia tasks
        self._running = True
        self._capture_task = asyncio.create_task(self._capture_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._upload_task = asyncio.create_task(self._upload_buffer_loop())
        
        # Conecta WebSocket para configuração remota
        if self.ws_client:
            asyncio.create_task(self.ws_client.connect())
        
        print("\n[Agent] Agente iniciado com sucesso!")
        print(f"[Agent] Device ID: {self.config.device_id}")
        print(f"[Agent] Provider: {self.capture_manager.get_provider_name()}")
        print(f"[Agent] Sampling: {self.config.sampling_interval}s")
        print("="*60 + "\n")
    
    async def stop(self) -> None:
        """Para o agente"""
        print("\n[Agent] Parando agente...")
        
        self._running = False
        
        # Cancela tasks
        if self._capture_task:
            self._capture_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._upload_task:
            self._upload_task.cancel()
        
        # Para módulos
        if self.capture_manager:
            await self.capture_manager.stop()
        
        if self.ws_client:
            await self.ws_client.disconnect()
        
        if self.http_client:
            await self.http_client.close()
        
        print("[Agent] Agente parado")
    
    async def _init_modules(self) -> None:
        """Inicializa todos os módulos"""
        # Capture Manager
        self.capture_manager = CaptureManager(self.config.provider_type)
        await self.capture_manager.start()
        
        # Feature Extractor
        self.feature_extractor = FeatureExtractor()
        
        # Buffer Manager
        self.buffer_manager = BufferManager(
            db_path=self.config.buffer_db_path,
            max_size_mb=self.config.buffer_max_size_mb
        )
        
        # HTTP Client
        self.http_client = HTTPClient(
            backend_url=self.config.backend_url,
            jwt_token=self.config.jwt_token,
            retry_max_attempts=self.config.retry_max_attempts,
            retry_backoff_base=self.config.retry_backoff_base,
            retry_initial_delay=self.config.retry_initial_delay
        )
        
        # WebSocket Client
        self.ws_client = WebSocketClient(
            websocket_url=self.config.websocket_url,
            jwt_token=self.config.jwt_token,
            on_config_update=self._handle_config_update
        )
    
    async def _activate_device(self) -> None:
        """
        Ativa o dispositivo solicitando activation_key ao usuário.
        """
        print("\n" + "="*60)
        print("ATIVAÇÃO DO DISPOSITIVO")
        print("="*60)
        
        # Detecta hardware
        print("\n[1/3] Detectando hardware...")
        hardware_info = HardwareDetector.detect_hardware()
        HardwareDetector.print_hardware_info()
        
        # Solicita activation_key
        print("[2/3] Solicitando chave de ativação...")
        activation_key = input("\nDigite a chave de ativação: ").strip()
        
        if not activation_key:
            print("\n[Erro] Chave de ativação não fornecida!")
            raise RuntimeError("Activation key required")
        
        # Registra dispositivo
        print("\n[3/3] Registrando dispositivo no backend...")
        
        try:
            # Cria cliente HTTP temporário (sem JWT)
            temp_client = HTTPClient(backend_url=self.config.backend_url)
            
            # Registra dispositivo
            response = await temp_client.register_device(
                activation_key=activation_key,
                hardware_info=hardware_info
            )
            
            await temp_client.close()
            
            # Salva credenciais
            self.config_manager.update_config(
                device_id=response['device_id'],
                device_name=response.get('device_name', 'WiFiSense Device'),
                jwt_token=response['jwt_token'],
                activation_key=activation_key
            )
            
            # Recarrega config
            self.config = self.config_manager.load_config()
            
            print("\n✓ Dispositivo ativado com sucesso!")
            print(f"  Device ID: {self.config.device_id}")
            print(f"  Device Name: {self.config.device_name}")
            print("="*60 + "\n")
        
        except Exception as e:
            print(f"\n[Erro] Falha ao ativar dispositivo: {e}")
            raise
    
    async def _capture_loop(self) -> None:
        """
        Loop principal de captura e transmissão de dados.
        Captura sinais a cada sampling_interval segundos.
        """
        print("[Agent] Iniciando loop de captura...")
        
        while self._running:
            try:
                # Captura sinal
                signal = await self.capture_manager.capture_signal()
                
                # Extrai features
                features = self.feature_extractor.extract_features(signal)
                
                # Tenta enviar para o backend
                if await self._send_data(features):
                    # Sucesso - está online
                    if not self._online:
                        print("[Agent] Conexão restaurada - online")
                        self._online = True
                else:
                    # Falha - está offline
                    if self._online:
                        print("[Agent] Conexão perdida - offline")
                        self._online = False
                    
                    # Adiciona ao buffer
                    self.buffer_manager.add_data(features)
                
                # Aguarda próximo sampling
                await asyncio.sleep(self.config.sampling_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Agent] Erro no loop de captura: {e}")
                await asyncio.sleep(self.config.sampling_interval)
    
    async def _send_data(self, features: Dict[str, Any]) -> bool:
        """
        Envia dados para o backend.
        
        Args:
            features: Features extraídas
        
        Returns:
            bool: True se enviado com sucesso, False se falhou
        """
        try:
            await self.http_client.send_data(
                device_id=self.config.device_id,
                features=features,
                compress=True
            )
            return True
        
        except Exception as e:
            # Falha silenciosa - será buffered
            return False
    
    async def _heartbeat_loop(self) -> None:
        """
        Loop de heartbeat.
        Envia heartbeat a cada heartbeat_interval segundos.
        """
        print("[Agent] Iniciando loop de heartbeat...")
        
        while self._running:
            try:
                # Coleta métricas de saúde
                health_metrics = self._collect_health_metrics()
                
                # Envia heartbeat
                await self.http_client.send_heartbeat(
                    device_id=self.config.device_id,
                    health_metrics=health_metrics
                )
                
                # Aguarda próximo heartbeat
                await asyncio.sleep(self.config.heartbeat_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Agent] Erro no heartbeat: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
    
    def _collect_health_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas de saúde do sistema.
        
        Returns:
            Dict com cpu_percent, memory_mb, disk_percent
        """
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_mb': psutil.virtual_memory().used / (1024 * 1024),
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().timestamp()
        }
    
    async def _upload_buffer_loop(self) -> None:
        """
        Loop de upload de dados buffered.
        Verifica periodicamente se há dados pendentes e tenta enviar.
        """
        print("[Agent] Iniciando loop de upload de buffer...")
        
        while self._running:
            try:
                # Aguarda 60 segundos
                await asyncio.sleep(60)
                
                # Verifica se está online e há dados pendentes
                if self._online and self.buffer_manager.get_pending_count() > 0:
                    await self._upload_buffered_data()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Agent] Erro no upload de buffer: {e}")
    
    async def _upload_buffered_data(self) -> None:
        """
        Faz upload de dados buffered para o backend.
        """
        print("[Agent] Iniciando upload de dados buffered...")
        
        # Busca dados pendentes em lotes de 100
        pending = self.buffer_manager.get_pending_data(limit=100)
        
        if not pending:
            return
        
        try:
            # Prepara batch com timestamps originais
            batch = [
                {
                    'features': item['features'],
                    'timestamp': item['timestamp']
                }
                for item in pending
            ]
            
            # Envia batch
            await self.http_client.send_batch_data(
                device_id=self.config.device_id,
                batch=batch,
                compress=True
            )
            
            # Marca como uploaded
            record_ids = [item['id'] for item in pending]
            self.buffer_manager.mark_as_uploaded(record_ids)
            
            # Limpa dados uploaded
            deleted = self.buffer_manager.clear_uploaded_data()
            
            print(f"[Agent] Upload concluído: {len(pending)} registros, {deleted} removidos")
        
        except Exception as e:
            print(f"[Agent] Erro ao fazer upload de buffer: {e}")
    
    def _handle_config_update(self, config: Dict[str, Any]) -> None:
        """
        Callback chamado quando recebe atualização de configuração via WebSocket.
        
        Args:
            config: Nova configuração recebida
        """
        print(f"[Agent] Recebida atualização de configuração: {config}")
        
        # Valida configuração
        if not self._validate_config(config):
            print("[Agent] Configuração inválida - rejeitada")
            return
        
        # Aplica configuração
        try:
            # Atualiza campos permitidos
            if 'sampling_interval' in config:
                self.config.sampling_interval = config['sampling_interval']
            
            if 'presence_threshold' in config:
                self.config.presence_threshold = config['presence_threshold']
            
            if 'movement_threshold' in config:
                self.config.movement_threshold = config['movement_threshold']
            
            if 'fall_threshold' in config:
                self.config.fall_threshold = config['fall_threshold']
            
            # Salva configuração
            self.config_manager.save_config(self.config)
            
            print("[Agent] Configuração aplicada com sucesso")
        
        except Exception as e:
            print(f"[Agent] Erro ao aplicar configuração: {e}")
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida parâmetros de configuração.
        
        Args:
            config: Configuração a validar
        
        Returns:
            bool: True se válida, False caso contrário
        """
        # Valida sampling_interval
        if 'sampling_interval' in config:
            if not isinstance(config['sampling_interval'], (int, float)):
                return False
            if config['sampling_interval'] < 1 or config['sampling_interval'] > 10:
                return False
        
        # Valida thresholds
        for key in ['presence_threshold', 'movement_threshold', 'fall_threshold']:
            if key in config:
                if not isinstance(config[key], (int, float)):
                    return False
                if config[key] < 0 or config[key] > 1:
                    return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do agente.
        
        Returns:
            Dict com informações de status
        """
        buffer_stats = self.buffer_manager.get_stats() if self.buffer_manager else {}
        
        return {
            'running': self._running,
            'online': self._online,
            'device_id': self.config.device_id,
            'device_name': self.config.device_name,
            'provider': self.capture_manager.get_provider_name() if self.capture_manager else None,
            'sampling_interval': self.config.sampling_interval,
            'buffer': buffer_stats,
            'websocket_connected': self.ws_client.is_connected() if self.ws_client else False
        }
