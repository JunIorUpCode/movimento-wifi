#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WiFiSense Agent - Script Principal
Ponto de entrada para executar o agente local
"""

import asyncio
import signal
import sys
from pathlib import Path

from agent.agent import WiFiSenseAgent


def signal_handler(agent: WiFiSenseAgent):
    """Handler para sinais de interrupção (Ctrl+C, SIGTERM)"""
    def handler(signum, frame):
        print("\n[Main] Sinal de interrupção recebido, parando agente...")
        asyncio.create_task(agent.stop())
        sys.exit(0)
    
    return handler


async def main():
    """Função principal"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    WiFiSense Agent v1.0                      ║
║                                                              ║
║          Agente Local para Monitoramento Wi-Fi               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Cria agente
    agent = WiFiSenseAgent()
    
    # Configura handler de sinais
    signal.signal(signal.SIGINT, signal_handler(agent))
    signal.signal(signal.SIGTERM, signal_handler(agent))
    
    try:
        # Inicia agente
        await agent.start()
        
        # Mantém rodando
        while True:
            await asyncio.sleep(1)
            
            # Exibe status periodicamente (a cada 60s)
            if int(asyncio.get_event_loop().time()) % 60 == 0:
                status = agent.get_status()
                print(f"\n[Status] Online: {status['online']} | "
                      f"Buffer: {status['buffer']['pending_count']} pendentes | "
                      f"WS: {'conectado' if status['websocket_connected'] else 'desconectado'}")
    
    except KeyboardInterrupt:
        print("\n[Main] Interrompido pelo usuário")
    
    except Exception as e:
        print(f"\n[Main] Erro fatal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Para agente
        await agent.stop()


if __name__ == "__main__":
    # Executa agente
    asyncio.run(main())
