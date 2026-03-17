"""
Script de teste para captura de sinais Wi-Fi reais no Windows.
Execute este script para testar se consegue capturar sinais reais.
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório app ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.capture.rssi_windows import RssiWindowsProvider


async def test_wifi_capture():
    """Testa captura de sinais Wi-Fi reais."""
    
    print("=" * 60)
    print("  TESTE DE CAPTURA DE SINAIS WI-FI REAIS")
    print("=" * 60)
    print()
    
    # Cria provider
    provider = RssiWindowsProvider()
    
    print("[1/3] Iniciando provider...")
    await provider.start()
    print(f"✓ Provider iniciado")
    print(f"  Interface: {provider._interface_name}")
    print(f"  Rede alvo: {provider.target_ssid}")
    print()
    
    print("[2/3] Capturando sinais (10 amostras)...")
    print("-" * 60)
    
    for i in range(10):
        signal = await provider.get_signal()
        
        print(f"Amostra {i+1:2d}: RSSI = {signal.rssi:6.2f} dBm | "
              f"Timestamp = {signal.timestamp:.2f}")
        
        await asyncio.sleep(1)
    
    print("-" * 60)
    print()
    
    print("[3/3] Parando provider...")
    await provider.stop()
    print("✓ Provider parado")
    print()
    
    print("=" * 60)
    print("  TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print()
    print("PRÓXIMOS PASSOS:")
    print("1. Se viu valores de RSSI variando, a captura está funcionando!")
    print("2. Edite backend/app/services/monitor_service.py")
    print("3. Substitua MockSignalProvider por RssiWindowsProvider")
    print("4. Reinicie o backend")
    print()


if __name__ == '__main__':
    try:
        asyncio.run(test_wifi_capture())
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n\nERRO: {e}")
        import traceback
        traceback.print_exc()
