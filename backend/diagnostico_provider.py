"""
Script de diagnóstico para testar a auto-detecção de providers.

Execute este script para verificar qual provider será usado no seu sistema.
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.capture.provider_factory import ProviderFactory


async def main():
    """Testa a detecção automática de providers."""
    
    print("=" * 70)
    print("DIAGNÓSTICO DE PROVIDERS - WiFiSense")
    print("=" * 70)
    print()
    
    # 1. Informações do sistema
    print("📊 INFORMAÇÕES DO SISTEMA")
    print("-" * 70)
    info = ProviderFactory.get_provider_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # 2. Providers disponíveis
    print("🔍 PROVIDERS DISPONÍVEIS")
    print("-" * 70)
    available = ProviderFactory.get_available_providers()
    for provider, is_available in available.items():
        status = "✓ Disponível" if is_available else "✗ Não disponível"
        print(f"  {provider:20s} {status}")
    print()
    
    # 3. Provider que será usado
    print("🎯 PROVIDER SELECIONADO")
    print("-" * 70)
    provider = ProviderFactory.create_provider()
    print(f"  Tipo: {provider.__class__.__name__}")
    print(f"  Disponível: {provider.is_available()}")
    print()
    
    # 4. Teste de captura
    print("🧪 TESTE DE CAPTURA")
    print("-" * 70)
    try:
        await provider.start()
        print("  ✓ Provider iniciado com sucesso")
        
        signal = await provider.get_signal()
        print(f"  ✓ Sinal capturado:")
        print(f"    - RSSI: {signal.rssi:.1f} dBm")
        print(f"    - CSI: {len(signal.csi_amplitude)} subportadoras")
        print(f"    - Provider: {signal.provider}")
        print(f"    - Timestamp: {signal.timestamp}")
        if signal.metadata:
            print(f"    - Metadata: {signal.metadata}")
        
        await provider.stop()
        print("  ✓ Provider parado com sucesso")
    
    except Exception as e:
        print(f"  ✗ Erro ao testar provider: {e}")
    
    print()
    
    # 5. Recomendações
    print("💡 RECOMENDAÇÕES")
    print("-" * 70)
    
    if available['csi']:
        print("  ✓ Sistema configurado com CSI - melhor qualidade possível!")
        print("  ✓ Você pode oferecer o plano PREMIUM aos clientes")
    
    elif available['rssi_windows']:
        print("  ✓ Sistema Windows detectado - RSSI funcionando")
        print("  ℹ Para melhor qualidade, considere hardware com CSI")
        print("  ✓ Você pode oferecer o plano BÁSICO aos clientes")
    
    elif available['rssi_linux']:
        print("  ✓ Sistema Linux detectado - RSSI funcionando")
        print("  ℹ Para melhor qualidade, considere hardware com CSI")
        print("  ✓ Você pode oferecer o plano BÁSICO aos clientes")
    
    else:
        print("  ⚠ Nenhum hardware real detectado - usando simulação")
        print("  📝 Para Linux/Raspberry Pi, instale:")
        print("     sudo apt-get install wireless-tools iw")
        print("  📝 Para Windows: nenhuma instalação necessária")
        print("  📝 Para CSI: hardware específico necessário")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
