#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Uso do Agente WiFiSense
Demonstra como usar o agente em modo standalone (sem backend)
"""

import asyncio
import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.capture import CaptureManager
from agent.processing import FeatureExtractor
from agent.storage import BufferManager
from agent.hardware_detector import HardwareDetector


async def example_1_hardware_detection():
    """
    Exemplo 1: Detecção de Hardware
    Mostra como detectar automaticamente as capacidades do hardware
    """
    print("\n" + "="*60)
    print("EXEMPLO 1: Detecção de Hardware")
    print("="*60)
    
    # Detecta hardware
    hardware_info = HardwareDetector.detect_hardware()
    
    # Exibe informações
    HardwareDetector.print_hardware_info()
    
    # Verifica capacidades
    if hardware_info['csi_capable']:
        print("✓ Este dispositivo suporta CSI - recomendado plano PREMIUM")
    else:
        print("ℹ Este dispositivo suporta apenas RSSI - plano BÁSICO")


async def example_2_signal_capture():
    """
    Exemplo 2: Captura de Sinais
    Mostra como capturar sinais Wi-Fi em tempo real
    """
    print("\n" + "="*60)
    print("EXEMPLO 2: Captura de Sinais Wi-Fi")
    print("="*60)
    
    # Cria gerenciador de captura (usa mock para exemplo)
    manager = CaptureManager(provider_type='mock')
    await manager.start()
    
    print(f"\nProvider: {manager.get_provider_name()}")
    print("\nCapturando 10 sinais...\n")
    
    # Captura 10 sinais
    for i in range(10):
        signal = await manager.capture_signal()
        
        print(f"Sinal {i+1:2d}: "
              f"RSSI={signal.rssi:6.1f} dBm | "
              f"CSI={len(signal.csi_amplitude):2d} subportadoras | "
              f"Provider={signal.provider}")
        
        await asyncio.sleep(0.5)
    
    await manager.stop()


async def example_3_feature_extraction():
    """
    Exemplo 3: Extração de Features
    Mostra como processar sinais e extrair features
    """
    print("\n" + "="*60)
    print("EXEMPLO 3: Extração de Features")
    print("="*60)
    
    # Cria gerenciador e extrator
    manager = CaptureManager(provider_type='mock')
    await manager.start()
    
    extractor = FeatureExtractor()
    
    print("\nProcessando 10 sinais...\n")
    
    # Processa 10 sinais
    for i in range(10):
        signal = await manager.capture_signal()
        features = extractor.extract_features(signal)
        
        print(f"Sinal {i+1:2d}:")
        print(f"  RSSI normalizado: {features['rssi_normalized']:.3f}")
        print(f"  Variância:        {features['signal_variance']:.3f}")
        print(f"  Energia:          {features['signal_energy']:.3f}")
        print(f"  Instabilidade:    {features['instability_score']:.3f}")
        print(f"  Taxa de mudança:  {features['rate_of_change']:.3f}")
        print()
        
        await asyncio.sleep(0.5)
    
    await manager.stop()


async def example_4_buffer_management():
    """
    Exemplo 4: Gerenciamento de Buffer
    Mostra como usar o buffer para armazenar dados offline
    """
    print("\n" + "="*60)
    print("EXEMPLO 4: Gerenciamento de Buffer Offline")
    print("="*60)
    
    # Cria buffer temporário
    buffer = BufferManager(db_path="example_buffer.db", max_size_mb=1)
    
    print("\n1. Adicionando dados ao buffer...")
    
    # Adiciona 20 registros
    for i in range(20):
        features = {
            'timestamp': i,
            'rssi_normalized': 0.5 + i * 0.01,
            'signal_variance': 0.1,
            'signal_energy': 0.2,
            'instability_score': 0.05
        }
        buffer.add_data(features)
    
    # Exibe estatísticas
    stats = buffer.get_stats()
    print(f"\n2. Estatísticas do buffer:")
    print(f"   Tamanho: {stats['size_mb']:.3f} MB / {stats['max_size_mb']:.0f} MB")
    print(f"   Pendentes: {stats['pending_count']}")
    print(f"   Uploaded: {stats['uploaded_count']}")
    
    # Busca dados pendentes
    print(f"\n3. Buscando dados pendentes (limite 10)...")
    pending = buffer.get_pending_data(limit=10)
    print(f"   Encontrados: {len(pending)} registros")
    
    # Simula upload
    print(f"\n4. Simulando upload...")
    record_ids = [item['id'] for item in pending]
    buffer.mark_as_uploaded(record_ids)
    print(f"   Marcados como uploaded: {len(record_ids)} registros")
    
    # Limpa uploaded
    print(f"\n5. Limpando dados uploaded...")
    deleted = buffer.clear_uploaded_data()
    print(f"   Removidos: {deleted} registros")
    
    # Estatísticas finais
    stats = buffer.get_stats()
    print(f"\n6. Estatísticas finais:")
    print(f"   Pendentes: {stats['pending_count']}")
    print(f"   Uploaded: {stats['uploaded_count']}")
    
    # Limpa arquivo de exemplo
    import os
    from pathlib import Path
    db_path = Path.home() / ".wifisense_agent" / "example_buffer.db"
    if db_path.exists():
        os.remove(db_path)
        print(f"\n7. Arquivo de exemplo removido")


async def example_5_complete_workflow():
    """
    Exemplo 5: Fluxo Completo
    Demonstra o fluxo completo: captura → processamento → buffer
    """
    print("\n" + "="*60)
    print("EXEMPLO 5: Fluxo Completo (Captura → Processamento → Buffer)")
    print("="*60)
    
    # Inicializa componentes
    manager = CaptureManager(provider_type='mock')
    await manager.start()
    
    extractor = FeatureExtractor()
    buffer = BufferManager(db_path="workflow_buffer.db", max_size_mb=1)
    
    print("\nSimulando 5 segundos de captura...\n")
    
    # Simula 5 segundos de captura
    for i in range(5):
        # 1. Captura sinal
        signal = await manager.capture_signal()
        
        # 2. Extrai features
        features = extractor.extract_features(signal)
        
        # 3. Adiciona ao buffer (simula offline)
        buffer.add_data(features)
        
        print(f"[{i+1}s] Capturado → Processado → Buffered")
        print(f"      RSSI: {signal.rssi:.1f} dBm | "
              f"Variância: {features['signal_variance']:.3f} | "
              f"Energia: {features['signal_energy']:.3f}")
        
        await asyncio.sleep(1)
    
    # Estatísticas finais
    stats = buffer.get_stats()
    print(f"\n✓ Fluxo completo executado com sucesso!")
    print(f"  Dados buffered: {stats['pending_count']} registros")
    print(f"  Tamanho: {stats['size_mb']:.3f} MB")
    
    # Cleanup
    await manager.stop()
    
    import os
    from pathlib import Path
    db_path = Path.home() / ".wifisense_agent" / "workflow_buffer.db"
    if db_path.exists():
        os.remove(db_path)


async def main():
    """Executa todos os exemplos"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           WiFiSense Agent - Exemplos de Uso                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Executa exemplos
    await example_1_hardware_detection()
    await example_2_signal_capture()
    await example_3_feature_extraction()
    await example_4_buffer_management()
    await example_5_complete_workflow()
    
    print("\n" + "="*60)
    print("Todos os exemplos executados com sucesso!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
