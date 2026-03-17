"""
Script para iniciar o sistema WiFiSense COMPLETO com Telegram configurado.

Este script:
1. Configura o Telegram com suas credenciais
2. Inicia o monitoramento REAL de Wi-Fi
3. Sistema detecta movimento/queda e envia alertas automaticamente
"""

import asyncio
import httpx
import time


async def configurar_e_iniciar():
    """Configura Telegram e inicia monitoramento."""
    
    BASE_URL = "http://localhost:8000/api"
    
    print("="*70)
    print("INICIANDO SISTEMA WIFISENSE COMPLETO")
    print("="*70)
    
    # Suas credenciais do Telegram
    BOT_TOKEN = "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA"
    CHAT_ID = "2085218769"
    
    print(f"\n📱 Bot: @zelarupcode_bot")
    print(f"📱 Chat ID: {CHAT_ID}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Passo 1: Configurar Telegram
        print("\n[1/4] Configurando Telegram no sistema...")
        config_data = {
            "enabled": True,
            "channels": ["telegram"],
            "telegram_bot_token": BOT_TOKEN,
            "telegram_chat_ids": [CHAT_ID],
            "min_confidence": 0.7,  # 70% de confiança mínima
            "cooldown_seconds": 60,  # 1 minuto entre alertas do mesmo tipo
            "quiet_hours": []  # Sem horário de silêncio
        }
        
        try:
            response = await client.put(
                f"{BASE_URL}/notifications/config",
                json=config_data
            )
            
            if response.status_code == 200:
                print("✅ Telegram configurado com sucesso!")
                config = response.json()
                print(f"   - Canais ativos: {config['channels']}")
                print(f"   - Confiança mínima: {config['min_confidence']*100:.0f}%")
                print(f"   - Cooldown: {config['cooldown_seconds']}s")
            else:
                print(f"❌ Erro ao configurar: {response.status_code}")
                print(f"   {response.text}")
                return
        except Exception as e:
            print(f"❌ Erro: {e}")
            return
        
        # Passo 2: Testar Telegram
        print("\n[2/4] Testando envio para Telegram...")
        test_data = {
            "channel": "telegram",
            "message": "🎉 Sistema WiFiSense iniciado!\n\nVocê receberá alertas de:\n• Quedas detectadas\n• Inatividade prolongada\n• Movimento suspeito\n• Anomalias"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/notifications/test",
                json=test_data
            )
            
            if response.status_code == 200:
                print("✅ Mensagem de teste enviada!")
                print("   📱 Verifique seu Telegram agora!")
            else:
                print(f"⚠️  Aviso: {response.status_code}")
                print(f"   {response.text}")
        except Exception as e:
            print(f"⚠️  Aviso: {e}")
        
        # Aguarda um pouco
        await asyncio.sleep(2)
        
        # Passo 3: Iniciar monitoramento
        print("\n[3/4] Iniciando monitoramento de Wi-Fi...")
        try:
            response = await client.post(f"{BASE_URL}/monitor/start")
            
            if response.status_code == 200:
                print("✅ Monitoramento iniciado!")
                print("\n📡 Sistema está capturando sinais Wi-Fi REAIS")
                print("🔍 Detectando movimento, quedas e anomalias")
                print("📱 Alertas serão enviados para seu Telegram")
            else:
                print(f"❌ Erro ao iniciar: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Erro: {e}")
            return
        
        # Passo 4: Monitorar status
        print("\n[4/4] Monitorando sistema...")
        print("\n" + "="*70)
        print("SISTEMA ATIVO - Monitorando ambiente")
        print("="*70)
        print("\nPressione Ctrl+C para parar\n")
        
        try:
            while True:
                # Consulta status a cada 5 segundos
                response = await client.get(f"{BASE_URL}/status")
                
                if response.status_code == 200:
                    status = response.json()
                    
                    # Limpa linha anterior
                    print("\r" + " "*100, end="")
                    
                    # Mostra status atual
                    event = status['current_event']
                    confidence = status['confidence'] * 100
                    signal = status.get('signal_data') or {}
                    rssi = signal.get('rssi', 0) if signal else 0
                    
                    # Emoji baseado no evento
                    emoji_map = {
                        'no_presence': '⚪',
                        'presence_still': '🟢',
                        'presence_moving': '🔵',
                        'fall_suspected': '🔴',
                        'prolonged_inactivity': '🟡',
                        'anomaly_detected': '🟣'
                    }
                    emoji = emoji_map.get(event, '⚪')
                    
                    # Tradução dos eventos
                    event_names = {
                        'no_presence': 'Sem presença',
                        'presence_still': 'Presença parada',
                        'presence_moving': 'Movimento',
                        'fall_suspected': '🚨 QUEDA SUSPEITA',
                        'prolonged_inactivity': '⏰ Inatividade',
                        'anomaly_detected': '📊 Anomalia'
                    }
                    event_name = event_names.get(event, event)
                    
                    print(f"\r{emoji} {event_name} | Confiança: {confidence:.0f}% | RSSI: {rssi:.1f} dBm", end="", flush=True)
                
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Parando sistema...")
            
            # Para o monitoramento
            try:
                response = await client.post(f"{BASE_URL}/monitor/stop")
                if response.status_code == 200:
                    print("✅ Sistema parado com sucesso!")
            except Exception as e:
                print(f"⚠️  Aviso ao parar: {e}")
    
    print("\n" + "="*70)
    print("SISTEMA ENCERRADO")
    print("="*70)


async def main():
    """Função principal."""
    
    print("\n🚀 WiFiSense - Sistema de Detecção por Wi-Fi")
    print("📡 Captura REAL de sinais Wi-Fi")
    print("🤖 Detecção inteligente de eventos")
    print("📱 Alertas via Telegram\n")
    
    # Verifica se backend está rodando
    print("Verificando se backend está rodando...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                print("✅ Backend está rodando!\n")
            else:
                print("❌ Backend não está respondendo corretamente")
                print("   Execute: uvicorn app.main:app --reload")
                return
    except Exception as e:
        print("❌ Backend não está rodando!")
        print("   Execute: uvicorn app.main:app --reload")
        print(f"   Erro: {e}")
        return
    
    # Inicia sistema
    await configurar_e_iniciar()


if __name__ == "__main__":
    asyncio.run(main())
