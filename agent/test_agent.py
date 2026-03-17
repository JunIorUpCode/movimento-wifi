#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários do Agente Local WiFiSense
Testa ativação, captura, compressão, buffer e heartbeat
"""

import asyncio
import sys
import os
import pytest
import tempfile
import gzip
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.hardware_detector import HardwareDetector
from agent.capture import CaptureManager
from agent.processing import FeatureExtractor
from agent.storage import BufferManager
from agent.config import ConfigManager, AgentConfig
from agent.api_client import HTTPClient
from agent.agent import WiFiSenseAgent


# ============================================================================
# TESTES DE ATIVAÇÃO DE DISPOSITIVO (Requisitos 3.2, 3.3)
# ============================================================================

class TestDeviceActivation:
    """Testa ativação de dispositivo com chave válida"""
    
    @pytest.mark.asyncio
    async def test_activation_with_valid_key(self):
        """
        Testa ativação com chave válida
        Valida: Requisitos 3.2, 3.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigManager(config_dir=Path(tmpdir))
            
            # Mock do HTTPClient para simular resposta do backend
            with patch('agent.agent.HTTPClient') as MockHTTPClient:
                mock_http = AsyncMock()
                mock_http.register_device = AsyncMock(return_value={
                    'device_id': 'test-device-123',
                    'device_name': 'Test Device',
                    'jwt_token': 'test-jwt-token-456'
                })
                mock_http.close = AsyncMock()
                MockHTTPClient.return_value = mock_http
                
                # Simula entrada do usuário com chave válida
                with patch('builtins.input', return_value='VALID-ACTIVATION-KEY'):
                    agent = WiFiSenseAgent(config_dir=tmpdir)
                    
                    # Testa ativação
                    await agent._activate_device()
                    
                    # Verifica que device foi registrado
                    mock_http.register_device.assert_called_once()
                    call_args = mock_http.register_device.call_args
                    assert call_args[1]['activation_key'] == 'VALID-ACTIVATION-KEY'
                    assert 'hardware_info' in call_args[1]
                    
                    # Verifica que credenciais foram salvas
                    config = config_manager.load_config()
                    assert config.device_id == 'test-device-123'
                    assert config.device_name == 'Test Device'
                    assert config.jwt_token == 'test-jwt-token-456'
                    assert config.activation_key == 'VALID-ACTIVATION-KEY'
                    
                    # Verifica que está ativado
                    assert config_manager.is_activated() == True
    
    @pytest.mark.asyncio
    async def test_activation_with_invalid_key(self):
        """
        Testa ativação com chave inválida
        Valida: Requisito 3.2 (rejeição de chave inválida)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigManager(config_dir=Path(tmpdir))
            
            # Mock do HTTPClient para simular erro 403
            with patch('agent.agent.HTTPClient') as MockHTTPClient:
                mock_http = AsyncMock()
                mock_http.register_device = AsyncMock(
                    side_effect=Exception("403 Forbidden: Invalid activation key")
                )
                mock_http.close = AsyncMock()
                MockHTTPClient.return_value = mock_http
                
                # Simula entrada do usuário com chave inválida
                with patch('builtins.input', return_value='INVALID-KEY'):
                    agent = WiFiSenseAgent(config_dir=tmpdir)
                    
                    # Testa que ativação falha
                    with pytest.raises(Exception) as exc_info:
                        await agent._activate_device()
                    
                    assert "403 Forbidden" in str(exc_info.value)
                    
                    # Verifica que credenciais NÃO foram salvas
                    config = config_manager.load_config()
                    assert config.device_id is None
                    assert config.jwt_token is None
                    assert config_manager.is_activated() == False
    
    @pytest.mark.asyncio
    async def test_activation_includes_hardware_info(self):
        """
        Testa que ativação envia informações de hardware
        Valida: Requisito 3.4 (hardware metadata)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agent.agent.HTTPClient') as MockHTTPClient:
                mock_http = AsyncMock()
                mock_http.register_device = AsyncMock(return_value={
                    'device_id': 'test-device-123',
                    'jwt_token': 'test-jwt-token'
                })
                mock_http.close = AsyncMock()
                MockHTTPClient.return_value = mock_http
                
                with patch('builtins.input', return_value='TEST-KEY'):
                    agent = WiFiSenseAgent(config_dir=tmpdir)
                    await agent._activate_device()
                    
                    # Verifica que hardware_info foi enviado
                    call_args = mock_http.register_device.call_args[1]
                    hardware_info = call_args['hardware_info']
                    
                    assert 'type' in hardware_info
                    assert 'os' in hardware_info
                    assert 'wifi_adapter' in hardware_info
                    assert 'csi_capable' in hardware_info
                    assert 'architecture' in hardware_info


# ============================================================================
# TESTES DE CAPTURA E COMPRESSÃO (Requisitos 8.3, 8.4)
# ============================================================================

class TestSignalCaptureAndCompression:
    """Testa captura de sinais e compressão de dados"""
    
    @pytest.mark.asyncio
    async def test_signal_capture_extracts_features(self):
        """
        Testa que captura extrai features corretamente
        Valida: Requisito 8.3 (processamento local de features)
        """
        manager = CaptureManager(provider_type='mock')
        await manager.start()
        
        extractor = FeatureExtractor()
        
        # Captura sinal
        signal = await manager.capture_signal()
        features = extractor.extract_features(signal)
        
        # Verifica que features foram extraídas
        assert 'rssi_normalized' in features
        assert 'signal_variance' in features
        assert 'signal_energy' in features
        assert 'rate_of_change' in features
        assert 'instability_score' in features
        assert 'timestamp' in features
        
        # Verifica que valores são numéricos válidos
        assert isinstance(features['rssi_normalized'], (int, float))
        assert isinstance(features['signal_variance'], (int, float))
        assert isinstance(features['signal_energy'], (int, float))
        assert 0 <= features['rssi_normalized'] <= 1
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_data_compression_reduces_size(self):
        """
        Testa que compressão reduz tamanho dos dados
        Valida: Requisito 8.4 (compressão antes de transmissão)
        """
        # Cria dados de teste (features grandes)
        features = {
            'timestamp': datetime.now().timestamp(),
            'rssi_normalized': 0.75,
            'signal_variance': 0.123456789,
            'signal_energy': 0.987654321,
            'rate_of_change': 0.456789123,
            'instability_score': 0.321654987,
            'csi_amplitude': [0.1 * i for i in range(100)],  # Array grande
            'csi_phase': [0.2 * i for i in range(100)]
        }
        
        # Serializa sem compressão
        json_data = json.dumps(features, ensure_ascii=False).encode('utf-8')
        original_size = len(json_data)
        
        # Comprime
        compressed_data = gzip.compress(json_data)
        compressed_size = len(compressed_data)
        
        # Verifica que compressão reduziu tamanho
        assert compressed_size < original_size
        compression_ratio = compressed_size / original_size
        assert compression_ratio < 0.8  # Pelo menos 20% de redução
        
        # Verifica que descompressão recupera dados originais
        decompressed_data = gzip.decompress(compressed_data)
        recovered_features = json.loads(decompressed_data.decode('utf-8'))
        assert recovered_features == features
    
    @pytest.mark.asyncio
    async def test_http_client_compresses_data(self):
        """
        Testa que HTTPClient comprime dados antes de enviar
        Valida: Requisito 8.4
        """
        client = HTTPClient(backend_url="https://test.com")
        
        features = {
            'timestamp': datetime.now().timestamp(),
            'rssi_normalized': 0.5,
            'signal_variance': 0.1,
            'csi_amplitude': [0.1 * i for i in range(50)]
        }
        
        # Testa método de compressão
        compressed = client._compress_data(features)
        
        # Verifica que retorna bytes
        assert isinstance(compressed, bytes)
        
        # Verifica que é menor que JSON original
        json_size = len(json.dumps(features).encode('utf-8'))
        assert len(compressed) < json_size
        
        # Verifica que pode descomprimir
        decompressed = gzip.decompress(compressed)
        recovered = json.loads(decompressed.decode('utf-8'))
        assert recovered == features
        
        await client.close()


# ============================================================================
# TESTES DE BUFFER LOCAL (Requisitos 8.6, 8.7, 31.1-31.8)
# ============================================================================

class TestLocalBuffer:
    """Testa buffer local durante offline e upload quando online"""
    
    def test_buffer_stores_data_during_offline(self):
        """
        Testa que buffer armazena dados durante offline
        Valida: Requisitos 31.1, 31.2, 31.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = BufferManager(
                db_path="test_buffer.db",
                max_size_mb=10,
                config_dir=Path(tmpdir)
            )
            
            # Adiciona dados simulando offline
            features_list = []
            for i in range(10):
                features = {
                    'timestamp': 1000.0 + i,
                    'rssi_normalized': 0.5 + i * 0.01,
                    'signal_variance': 0.1,
                    'signal_energy': 0.2
                }
                success = buffer.add_data(features)
                assert success == True
                features_list.append(features)
            
            # Verifica que dados foram armazenados
            stats = buffer.get_stats()
            assert stats['pending_count'] == 10
            assert stats['size_mb'] > 0
            
            # Verifica que pode recuperar dados
            pending = buffer.get_pending_data(limit=10)
            assert len(pending) == 10
            
            # Verifica que timestamps originais foram preservados
            for i, item in enumerate(pending):
                assert item['timestamp'] == 1000.0 + i
    
    def test_buffer_uploads_when_online(self):
        """
        Testa upload de dados buffered quando conexão restaurada
        Valida: Requisitos 31.4, 31.8, 8.6
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = BufferManager(
                db_path="test_buffer.db",
                max_size_mb=10,
                config_dir=Path(tmpdir)
            )
            
            # Adiciona dados durante offline
            for i in range(5):
                buffer.add_data({
                    'timestamp': 2000.0 + i,
                    'rssi_normalized': 0.6,
                    'signal_variance': 0.15
                })
            
            # Simula upload quando online
            pending = buffer.get_pending_data(limit=5)
            assert len(pending) == 5
            
            # Marca como uploaded
            record_ids = [item['id'] for item in pending]
            buffer.mark_as_uploaded(record_ids)
            
            # Verifica que foram marcados
            stats = buffer.get_stats()
            assert stats['uploaded_count'] == 5
            assert stats['pending_count'] == 0
            
            # Limpa dados uploaded
            deleted = buffer.clear_uploaded_data()
            assert deleted == 5
            
            # Verifica que buffer está vazio
            stats = buffer.get_stats()
            assert stats['uploaded_count'] == 0
    
    def test_buffer_preserves_chronological_order(self):
        """
        Testa que buffer mantém ordem cronológica
        Valida: Requisito 31.4 (upload em ordem cronológica)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = BufferManager(
                db_path="test_buffer.db",
                config_dir=Path(tmpdir)
            )
            
            # Adiciona dados em ordem cronológica (created_at determina ordem)
            timestamps = [1001.0, 1002.0, 1004.0, 1005.0, 1008.0]
            for ts in timestamps:
                buffer.add_data({
                    'timestamp': ts,
                    'rssi_normalized': 0.5
                })
            
            # Recupera dados
            pending = buffer.get_pending_data(limit=10)
            
            # Verifica que estão em ordem de inserção (created_at ASC)
            # que corresponde à ordem cronológica dos timestamps
            recovered_timestamps = [item['timestamp'] for item in pending]
            assert recovered_timestamps == timestamps
    
    def test_buffer_fifo_when_full(self):
        """
        Testa que buffer descarta dados mais antigos quando cheio (FIFO)
        Valida: Requisitos 31.5, 31.6
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Cria buffer muito pequeno (0.1 MB = 100 KB) para forçar overflow
            buffer = BufferManager(
                db_path="test_buffer.db",
                max_size_mb=0.1,
                config_dir=Path(tmpdir)
            )
            
            # Adiciona muitos dados para encher buffer
            initial_count = 0
            for i in range(200):
                features = {
                    'timestamp': 3000.0 + i,
                    'rssi_normalized': 0.5,
                    'signal_variance': 0.1,
                    'csi_amplitude': [0.1 * j for j in range(100)]  # Dados grandes
                }
                buffer.add_data(features)
                
                # Conta quantos registros foram adicionados antes do overflow
                if i == 50:
                    initial_count = buffer.get_pending_count()
            
            # Verifica que buffer não excedeu limite significativamente
            # (permite pequeno overhead do SQLite)
            stats = buffer.get_stats()
            assert stats['size_mb'] <= stats['max_size_mb'] * 1.1  # 10% overhead permitido
            
            # Verifica que dados mais recentes foram preservados
            pending = buffer.get_pending_data(limit=200)
            final_count = len(pending)
            
            # Deve ter descartado alguns registros (FIFO)
            assert final_count < 200
            
            # Timestamps devem ser dos dados mais recentes
            timestamps = [item['timestamp'] for item in pending]
            max_timestamp = max(timestamps)
            min_timestamp = min(timestamps)
            
            # O último registro adicionado deve estar presente
            assert max_timestamp == 3199.0
            
            # E dados antigos devem ter sido descartados
            # Se buffer está cheio, min_timestamp deve ser > 3000
            assert min_timestamp > 3000.0
    
    def test_buffer_survives_restart(self):
        """
        Testa que buffer persiste entre reinicializações
        Valida: Requisito 31.2 (SQLite persistente)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Primeira instância: adiciona dados
            buffer1 = BufferManager(
                db_path="test_buffer.db",
                config_dir=Path(tmpdir)
            )
            
            for i in range(5):
                buffer1.add_data({
                    'timestamp': 4000.0 + i,
                    'rssi_normalized': 0.7
                })
            
            stats1 = buffer1.get_stats()
            assert stats1['pending_count'] == 5
            
            # Simula reinicialização: nova instância com mesmo arquivo
            buffer2 = BufferManager(
                db_path="test_buffer.db",
                config_dir=Path(tmpdir)
            )
            
            # Verifica que dados persistiram
            stats2 = buffer2.get_stats()
            assert stats2['pending_count'] == 5
            
            pending = buffer2.get_pending_data(limit=10)
            assert len(pending) == 5
            
            # Verifica timestamps
            timestamps = [item['timestamp'] for item in pending]
            assert timestamps == [4000.0 + i for i in range(5)]


# ============================================================================
# TESTES DE HEARTBEAT (Requisitos 39.1, 39.6)
# ============================================================================

class TestHeartbeat:
    """Testa funcionalidade de heartbeat"""
    
    @pytest.mark.asyncio
    async def test_heartbeat_includes_health_metrics(self):
        """
        Testa que heartbeat inclui métricas de saúde
        Valida: Requisito 39.6
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = WiFiSenseAgent(config_dir=tmpdir)
            
            # Coleta métricas de saúde
            metrics = agent._collect_health_metrics()
            
            # Verifica que métricas estão presentes
            assert 'cpu_percent' in metrics
            assert 'memory_mb' in metrics
            assert 'disk_percent' in metrics
            assert 'timestamp' in metrics
            
            # Verifica que valores são válidos
            assert isinstance(metrics['cpu_percent'], (int, float))
            assert isinstance(metrics['memory_mb'], (int, float))
            assert isinstance(metrics['disk_percent'], (int, float))
            assert metrics['cpu_percent'] >= 0
            assert metrics['memory_mb'] > 0
            assert 0 <= metrics['disk_percent'] <= 100
    
    @pytest.mark.asyncio
    async def test_heartbeat_sent_every_60_seconds(self):
        """
        Testa que heartbeat é enviado a cada 60 segundos
        Valida: Requisito 39.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock do HTTPClient
            with patch('agent.agent.HTTPClient') as MockHTTPClient:
                mock_http = AsyncMock()
                mock_http.send_heartbeat = AsyncMock()
                mock_http.close = AsyncMock()
                MockHTTPClient.return_value = mock_http
                
                # Configura agente
                config_manager = ConfigManager(config_dir=Path(tmpdir))
                config_manager.update_config(
                    device_id='test-device',
                    jwt_token='test-token',
                    heartbeat_interval=1  # 1 segundo para teste rápido
                )
                
                agent = WiFiSenseAgent(config_dir=tmpdir)
                await agent._init_modules()
                
                # Inicia loop de heartbeat
                agent._running = True
                heartbeat_task = asyncio.create_task(agent._heartbeat_loop())
                
                # Aguarda alguns heartbeats
                await asyncio.sleep(2.5)
                
                # Para o loop
                agent._running = False
                heartbeat_task.cancel()
                
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                
                # Verifica que heartbeat foi chamado múltiplas vezes
                assert mock_http.send_heartbeat.call_count >= 2
                
                # Verifica que device_id e health_metrics foram enviados
                call_args = mock_http.send_heartbeat.call_args[1]
                assert call_args['device_id'] == 'test-device'
                assert 'health_metrics' in call_args
                
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_heartbeat_continues_on_failure(self):
        """
        Testa que heartbeat continua mesmo se uma tentativa falhar
        Valida: Requisito 39.1 (resiliência)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agent.agent.HTTPClient') as MockHTTPClient:
                # Mock que falha na primeira chamada, sucede depois
                mock_http = AsyncMock()
                call_count = 0
                
                async def send_heartbeat_side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("Network error")
                    return {"status": "ok"}
                
                mock_http.send_heartbeat = AsyncMock(side_effect=send_heartbeat_side_effect)
                mock_http.close = AsyncMock()
                MockHTTPClient.return_value = mock_http
                
                config_manager = ConfigManager(config_dir=Path(tmpdir))
                config_manager.update_config(
                    device_id='test-device',
                    jwt_token='test-token',
                    heartbeat_interval=1
                )
                
                agent = WiFiSenseAgent(config_dir=tmpdir)
                await agent._init_modules()
                
                agent._running = True
                heartbeat_task = asyncio.create_task(agent._heartbeat_loop())
                
                # Aguarda tempo suficiente para múltiplas tentativas
                await asyncio.sleep(2.5)
                
                agent._running = False
                heartbeat_task.cancel()
                
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                
                # Verifica que continuou tentando após falha
                assert call_count >= 2
                
                await agent.stop()


# ============================================================================
# TESTES LEGADOS (mantidos para compatibilidade)
# ============================================================================

@pytest.mark.asyncio
async def test_hardware_detection():
    """Testa detecção de hardware"""
    print("\n" + "="*60)
    print("TESTE 1: Detecção de Hardware")
    print("="*60)
    
    try:
        hardware_info = HardwareDetector.detect_hardware()
        HardwareDetector.print_hardware_info()
        
        assert 'type' in hardware_info
        assert 'os' in hardware_info
        assert 'wifi_adapter' in hardware_info
        
        print("✓ Detecção de hardware OK")
        return True
    
    except Exception as e:
        print(f"✗ Erro na detecção de hardware: {e}")
        return False


@pytest.mark.asyncio
async def test_capture_manager():
    """Testa gerenciador de captura"""
    print("\n" + "="*60)
    print("TESTE 2: Gerenciador de Captura")
    print("="*60)
    
    try:
        # Usa provider mock para teste
        manager = CaptureManager(provider_type='mock')
        await manager.start()
        
        print(f"Provider: {manager.get_provider_name()}")
        
        # Captura 3 sinais
        for i in range(3):
            signal = await manager.capture_signal()
            print(f"  Sinal {i+1}: RSSI={signal.rssi:.1f} dBm, "
                  f"CSI={len(signal.csi_amplitude)} subportadoras")
        
        await manager.stop()
        
        print("✓ Gerenciador de captura OK")
        return True
    
    except Exception as e:
        print(f"✗ Erro no gerenciador de captura: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_feature_extractor():
    """Testa extrator de features"""
    print("\n" + "="*60)
    print("TESTE 3: Extrator de Features")
    print("="*60)
    
    try:
        manager = CaptureManager(provider_type='mock')
        await manager.start()
        
        extractor = FeatureExtractor()
        
        # Captura e processa 5 sinais
        for i in range(5):
            signal = await manager.capture_signal()
            features = extractor.extract_features(signal)
            
            print(f"  Sinal {i+1}:")
            print(f"    RSSI normalizado: {features['rssi_normalized']:.3f}")
            print(f"    Variância: {features['signal_variance']:.3f}")
            print(f"    Energia: {features['signal_energy']:.3f}")
            print(f"    Instabilidade: {features['instability_score']:.3f}")
        
        await manager.stop()
        
        print("✓ Extrator de features OK")
        return True
    
    except Exception as e:
        print(f"✗ Erro no extrator de features: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_buffer_manager():
    """Testa gerenciador de buffer"""
    print("\n" + "="*60)
    print("TESTE 4: Gerenciador de Buffer")
    print("="*60)
    
    try:
        # Cria buffer temporário
        buffer = BufferManager(db_path="test_buffer.db", max_size_mb=1)
        
        # Adiciona dados
        for i in range(10):
            features = {
                'timestamp': i,
                'rssi_normalized': 0.5 + i * 0.01,
                'signal_variance': 0.1,
                'signal_energy': 0.2
            }
            buffer.add_data(features)
        
        # Verifica estatísticas
        stats = buffer.get_stats()
        print(f"  Buffer size: {stats['size_mb']:.3f} MB")
        print(f"  Pending count: {stats['pending_count']}")
        
        # Busca dados pendentes
        pending = buffer.get_pending_data(limit=5)
        print(f"  Fetched: {len(pending)} registros")
        
        # Marca como uploaded
        record_ids = [item['id'] for item in pending]
        buffer.mark_as_uploaded(record_ids)
        
        # Limpa uploaded
        deleted = buffer.clear_uploaded_data()
        print(f"  Deleted: {deleted} registros")
        
        # Limpa arquivo de teste
        import os
        from pathlib import Path
        db_path = Path.home() / ".wifisense_agent" / "test_buffer.db"
        if db_path.exists():
            os.remove(db_path)
        
        print("✓ Gerenciador de buffer OK")
        return True
    
    except Exception as e:
        print(f"✗ Erro no gerenciador de buffer: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_config_manager():
    """Testa gerenciador de configuração"""
    print("\n" + "="*60)
    print("TESTE 5: Gerenciador de Configuração")
    print("="*60)
    
    try:
        from pathlib import Path
        import tempfile
        
        # Usa diretório temporário
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigManager(config_dir=Path(tmpdir))
            
            # Carrega config padrão
            config = config_manager.load_config()
            print(f"  Config padrão: sampling_interval={config.sampling_interval}s")
            
            # Atualiza config
            config_manager.update_config(
                device_id="test-device-123",
                jwt_token="test-token-456",
                sampling_interval=2
            )
            
            # Recarrega
            config = config_manager.load_config()
            print(f"  Config atualizada: device_id={config.device_id}")
            print(f"  JWT token: {'***' + config.jwt_token[-10:] if config.jwt_token else 'None'}")
            
            # Verifica ativação
            is_activated = config_manager.is_activated()
            print(f"  Ativado: {is_activated}")
            
            assert is_activated == True
            assert config.device_id == "test-device-123"
        
        print("✓ Gerenciador de configuração OK")
        return True
    
    except Exception as e:
        print(f"✗ Erro no gerenciador de configuração: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Executa todos os testes"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              WiFiSense Agent - Suite de Testes              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Executa testes
    results.append(await test_hardware_detection())
    results.append(await test_capture_manager())
    results.append(await test_feature_extractor())
    results.append(await test_buffer_manager())
    results.append(await test_config_manager())
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Testes passados: {passed}/{total}")
    
    if passed == total:
        print("\n✓ Todos os testes passaram!")
        return 0
    else:
        print(f"\n✗ {total - passed} teste(s) falharam")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
