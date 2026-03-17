# -*- coding: utf-8 -*-
"""
Cliente WebSocket para Configuração Remota
Recebe atualizações de configuração do backend em tempo real
"""

import asyncio
import json
from typing import Optional, Callable, Dict, Any
import aiohttp


class WebSocketClient:
    """
    Cliente WebSocket para receber configurações remotas.
    Conecta ao backend e recebe atualizações de configuração em tempo real.
    """
    
    def __init__(
        self,
        websocket_url: str,
        jwt_token: str,
        on_config_update: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Inicializa o cliente WebSocket.
        
        Args:
            websocket_url: URL do WebSocket (ex: wss://api.wifisense.com/ws)
            jwt_token: Token JWT para autenticação
            on_config_update: Callback chamado quando recebe atualização de config
        """
        self.websocket_url = websocket_url
        self.jwt_token = jwt_token
        self.on_config_update = on_config_update
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._reconnect_delay = 5.0
    
    async def connect(self) -> None:
        """
        Conecta ao WebSocket do backend.
        Implementa reconexão automática em caso de falha.
        """
        self._running = True
        
        while self._running:
            try:
                print(f"[WebSocketClient] Conectando a {self.websocket_url}")
                
                # Cria sessão se necessário
                if self._session is None or self._session.closed:
                    self._session = aiohttp.ClientSession()
                
                # Conecta ao WebSocket com autenticação
                self._ws = await self._session.ws_connect(
                    self.websocket_url,
                    headers={"Authorization": f"Bearer {self.jwt_token}"}
                )
                
                print("[WebSocketClient] Conectado com sucesso")
                
                # Loop de recepção de mensagens
                await self._receive_loop()
            
            except Exception as e:
                print(f"[WebSocketClient] Erro de conexão: {e}")
                
                if self._running:
                    print(f"[WebSocketClient] Reconectando em {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
    
    async def _receive_loop(self) -> None:
        """Loop de recepção de mensagens do WebSocket"""
        if not self._ws:
            return
        
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"[WebSocketClient] Erro no WebSocket: {self._ws.exception()}")
                    break
                
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("[WebSocketClient] Conexão fechada pelo servidor")
                    break
        
        except Exception as e:
            print(f"[WebSocketClient] Erro no loop de recepção: {e}")
    
    async def _handle_message(self, data: str) -> None:
        """
        Processa mensagem recebida do WebSocket.
        
        Args:
            data: Dados JSON da mensagem
        """
        try:
            message = json.loads(data)
            message_type = message.get('type')
            
            if message_type == 'config_update':
                # Atualização de configuração
                config = message.get('config', {})
                print(f"[WebSocketClient] Recebida atualização de configuração: {config}")
                
                if self.on_config_update:
                    self.on_config_update(config)
            
            elif message_type == 'ping':
                # Responde ao ping
                await self.send_pong()
            
            else:
                print(f"[WebSocketClient] Mensagem desconhecida: {message_type}")
        
        except json.JSONDecodeError as e:
            print(f"[WebSocketClient] Erro ao decodificar mensagem: {e}")
        except Exception as e:
            print(f"[WebSocketClient] Erro ao processar mensagem: {e}")
    
    async def send_pong(self) -> None:
        """Envia pong em resposta ao ping do servidor"""
        if self._ws and not self._ws.closed:
            try:
                await self._ws.send_json({"type": "pong"})
            except Exception as e:
                print(f"[WebSocketClient] Erro ao enviar pong: {e}")
    
    async def disconnect(self) -> None:
        """Desconecta do WebSocket"""
        self._running = False
        
        if self._ws and not self._ws.closed:
            await self._ws.close()
        
        if self._session and not self._session.closed:
            await self._session.close()
        
        print("[WebSocketClient] Desconectado")
    
    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self._ws is not None and not self._ws.closed
