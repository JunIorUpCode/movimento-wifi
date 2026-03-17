#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de Propriedade para Agente Local
Usa Hypothesis para validar propriedades do sistema
"""

import sys
import os
import json
import gzip
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hypothesis import given, strategies as st, settings
from hypothesis import assume
from agent.api_client.http_client import HTTPClient
from agent.storage.buffer_manager import BufferManager


class TestDataCompression:
    """
    Property 15: Data Compression Before Transmission
    Valida: Requisitos 8.4
    
    Verifica que o payload comprimido é menor que o payload original
    para garantir economia de banda na transmissão de dados.
    """
    
    @given(
        rssi_normalized=st.floats(min_value=0.0, max_value=1.0),
        signal_variance=st.floats(min_value=0.0, max_value=1.0),
        signal_energy=st.floats(min_value=0.0, max_value=10.0),
        rate_of_change=st.floats(min_value=-1.0, max_value=1.0),
        instability_score=st.floats(min_value=0.0, max_value=1.0),
        timestamp=st.floats(min_value=1000000000.0, max_value=2000000000.0)
    )
    @settings(max_examples=100)
    def test_compressed_payload_smaller_than_original(
        self,
        rssi_normalized,
        signal_variance,
        signal_energy,
        rate_of_change,
        instability_score,
        timestamp
    ):
        """
        PROPERTY: Payload comprimido deve ser menor que payload original
        
        Para qualquer conjunto de features válidas, quando comprimimos
        os dados com gzip, o tamanho do payload comprimido deve ser
        menor que o tamanho do payload original em JSON.
        
        Isso garante que a compressão está funcionando corretamente
        e economizando banda na transmissão.
        """
        # Cria payload de features típico
        features = {
            'timestamp': timestamp,
            'rssi_normalized': rssi_normalized,
            'signal_variance': signal_variance,
            'signal_energy': signal_energy,
            'rate_of_change': rate_of_change,
            'instability_score': instability_score,
            'metadata': {
                'device_type': 'test',
                'capture_method': 'mock'
            }
        }
        
        # Serializa para JSON (payload original)
        json_data = json.dumps(features, ensure_ascii=False).encode('utf-8')
        original_size = len(json_data)
        
        # Comprime com gzip (payload comprimido)
        compressed_data = gzip.compress(json_data)
        compressed_size = len(compressed_data)
        
        # PROPRIEDADE: Payload comprimido deve ser menor que original
        # Nota: Para dados muito pequenos, gzip pode aumentar o tamanho
        # devido ao overhead do header. Assumimos payloads > 100 bytes
        assume(original_size > 100)
        
        assert compressed_size < original_size, (
            f"Compressão falhou: original={original_size} bytes, "
            f"comprimido={compressed_size} bytes. "
            f"Compressão deveria reduzir o tamanho do payload."
        )
        
        # Verifica taxa de compressão razoável (pelo menos 10% de redução)
        compression_ratio = compressed_size / original_size
        assert compression_ratio < 0.9, (
            f"Taxa de compressão muito baixa: {compression_ratio:.2%}. "
            f"Esperado pelo menos 10% de redução."
        )
    
    @given(
        num_samples=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=50)
    def test_batch_compression_efficiency(self, num_samples):
        """
        PROPERTY: Compressão em batch é mais eficiente
        
        Quando comprimimos múltiplas amostras juntas (batch),
        a taxa de compressão deve ser melhor do que comprimir
        cada amostra individualmente, devido à redundância nos dados.
        """
        # Gera batch de samples
        batch = []
        for i in range(num_samples):
            sample = {
                'timestamp': 1000000000.0 + i,
                'rssi_normalized': 0.5 + (i % 10) * 0.01,
                'signal_variance': 0.1,
                'signal_energy': 0.2,
                'rate_of_change': 0.05,
                'instability_score': 0.3
            }
            batch.append(sample)
        
        # Comprime batch inteiro
        batch_json = json.dumps(batch, ensure_ascii=False).encode('utf-8')
        batch_compressed = gzip.compress(batch_json)
        batch_size = len(batch_compressed)
        
        # Comprime cada sample individualmente
        individual_total = 0
        for sample in batch:
            sample_json = json.dumps(sample, ensure_ascii=False).encode('utf-8')
            sample_compressed = gzip.compress(sample_json)
            individual_total += len(sample_compressed)
        
        # PROPRIEDADE: Batch comprimido deve ser menor que soma individual
        assert batch_size < individual_total, (
            f"Compressão em batch não é eficiente: "
            f"batch={batch_size} bytes, individual={individual_total} bytes"
        )
        
        # Calcula economia
        savings_percent = ((individual_total - batch_size) / individual_total) * 100
        
        # Deve economizar pelo menos 20% ao comprimir em batch
        assert savings_percent >= 20, (
            f"Economia de compressão em batch muito baixa: {savings_percent:.1f}%. "
            f"Esperado pelo menos 20% de economia."
        )
    
    def test_http_client_compress_method(self):
        """
        Testa o método _compress_data do HTTPClient
        """
        client = HTTPClient(backend_url="http://test.com")
        
        # Dados de teste (payload maior para garantir compressão efetiva)
        data = {
            'timestamp': 1234567890.0,
            'rssi_normalized': 0.75,
            'signal_variance': 0.15,
            'signal_energy': 0.25,
            'rate_of_change': 0.05,
            'instability_score': 0.3,
            'metadata': {
                'device_type': 'raspberry_pi',
                'capture_method': 'rssi',
                'hardware_info': {
                    'wifi_adapter': 'Intel 5300',
                    'os': 'Linux',
                    'version': '1.0.0'
                }
            }
        }
        
        # Comprime usando método do cliente
        compressed = client._compress_data(data)
        
        # Verifica que retorna bytes
        assert isinstance(compressed, bytes)
        
        # Verifica que pode descomprimir
        decompressed_json = gzip.decompress(compressed).decode('utf-8')
        decompressed_data = json.loads(decompressed_json)
        
        # Verifica que dados são preservados
        assert decompressed_data == data
        
        # Verifica que compressão reduziu tamanho (para payloads maiores)
        original_size = len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        compressed_size = len(compressed)
        
        # Para payloads maiores (>150 bytes), compressão deve reduzir tamanho
        if original_size > 150:
            assert compressed_size < original_size, (
                f"Compressão não reduziu tamanho: "
                f"original={original_size}, comprimido={compressed_size}"
            )


def run_property_tests():
    """
    Executa todos os testes de propriedade
    """
    import pytest
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         WiFiSense Agent - Testes de Propriedade             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("\nExecutando testes de propriedade com Hypothesis...\n")
    
    # Executa testes
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--hypothesis-show-statistics'
    ])
    
    return exit_code


class TestBufferedDataUpload:
    """
    Property 16: Offline Data Upload Round-Trip
    Valida: Requisitos 8.7
    
    Verifica que dados buffered durante offline são uploaded corretamente
    quando a conexão é restaurada, preservando timestamps originais.
    """
    
    @given(
        num_samples=st.integers(min_value=1, max_value=50),
        base_timestamp=st.floats(min_value=1000000000.0, max_value=2000000000.0)
    )
    @settings(max_examples=50, deadline=None)
    def test_buffered_data_preserves_original_timestamps(self, num_samples, base_timestamp):
        """
        PROPERTY: Timestamps originais devem ser preservados no round-trip
        
        Quando dados são buffered durante offline e depois uploaded,
        os timestamps originais devem ser preservados exatamente como
        foram capturados, não substituídos pelo timestamp do upload.
        
        Isso é crítico para análise temporal correta dos eventos.
        """
        # Cria diretório temporário para o teste
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Inicializa buffer manager
            buffer_manager = BufferManager(
                db_path="test_buffer.db",
                max_size_mb=10,
                config_dir=Path(temp_dir)
            )
            
            # Gera dados com timestamps incrementais
            original_data = []
            for i in range(num_samples):
                timestamp = base_timestamp + i * 1.0  # 1 segundo entre amostras
                features = {
                    'timestamp': timestamp,
                    'rssi_normalized': 0.5 + (i % 10) * 0.01,
                    'signal_variance': 0.1 + i * 0.001,
                    'signal_energy': 0.2,
                    'rate_of_change': 0.05,
                    'instability_score': 0.3
                }
                original_data.append(features)
            
            # FASE 1: OFFLINE - Buffer dados localmente
            for features in original_data:
                success = buffer_manager.add_data(features)
                assert success, "Falha ao adicionar dados ao buffer"
            
            # Verifica que dados foram buffered
            pending_count = buffer_manager.get_pending_count()
            assert pending_count == num_samples, (
                f"Número incorreto de dados pendentes: "
                f"esperado={num_samples}, atual={pending_count}"
            )
            
            # FASE 2: CONEXÃO RESTAURADA - Recupera dados do buffer
            buffered_data = buffer_manager.get_pending_data(limit=num_samples)
            
            # Verifica que recuperamos todos os dados
            assert len(buffered_data) == num_samples, (
                f"Número incorreto de dados recuperados: "
                f"esperado={num_samples}, recuperado={len(buffered_data)}"
            )
            
            # PROPRIEDADE: Timestamps originais devem ser preservados
            for i, buffered_record in enumerate(buffered_data):
                original_timestamp = original_data[i]['timestamp']
                buffered_timestamp = buffered_record['timestamp']
                
                assert buffered_timestamp == original_timestamp, (
                    f"Timestamp não preservado no índice {i}: "
                    f"original={original_timestamp}, buffered={buffered_timestamp}"
                )
                
                # Verifica que features também foram preservadas
                buffered_features = buffered_record['features']
                original_features = original_data[i]
                
                assert buffered_features['rssi_normalized'] == original_features['rssi_normalized']
                assert buffered_features['signal_variance'] == original_features['signal_variance']
            
            # FASE 3: UPLOAD - Marca como uploaded
            record_ids = [record['id'] for record in buffered_data]
            buffer_manager.mark_as_uploaded(record_ids)
            
            # Verifica que não há mais dados pendentes
            pending_after_upload = buffer_manager.get_pending_count()
            assert pending_after_upload == 0, (
                f"Ainda há dados pendentes após upload: {pending_after_upload}"
            )
            
            # FASE 4: CLEANUP - Remove dados uploaded
            deleted = buffer_manager.clear_uploaded_data()
            assert deleted == num_samples, (
                f"Número incorreto de registros deletados: "
                f"esperado={num_samples}, deletado={deleted}"
            )
        
        finally:
            # Limpa diretório temporário
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        num_samples=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_buffered_data_maintains_chronological_order(self, num_samples):
        """
        PROPERTY: Dados buffered devem manter ordem cronológica
        
        Quando múltiplos dados são buffered e depois recuperados,
        eles devem ser retornados na ordem cronológica original
        (ordenados por timestamp de captura).
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            buffer_manager = BufferManager(
                db_path="test_order.db",
                max_size_mb=10,
                config_dir=Path(temp_dir)
            )
            
            # Gera dados com timestamps aleatórios mas conhecidos
            base_timestamp = 1000000000.0
            timestamps = [base_timestamp + i * 10.0 for i in range(num_samples)]
            
            # Buffer dados
            for ts in timestamps:
                features = {
                    'timestamp': ts,
                    'rssi_normalized': 0.5,
                    'signal_variance': 0.1
                }
                buffer_manager.add_data(features)
            
            # Recupera dados
            buffered_data = buffer_manager.get_pending_data(limit=num_samples)
            
            # PROPRIEDADE: Dados devem estar em ordem cronológica
            recovered_timestamps = [record['timestamp'] for record in buffered_data]
            
            # Verifica que timestamps estão ordenados
            for i in range(len(recovered_timestamps) - 1):
                assert recovered_timestamps[i] <= recovered_timestamps[i + 1], (
                    f"Ordem cronológica violada no índice {i}: "
                    f"{recovered_timestamps[i]} > {recovered_timestamps[i + 1]}"
                )
            
            # Verifica que todos os timestamps originais estão presentes
            assert sorted(recovered_timestamps) == sorted(timestamps), (
                "Timestamps recuperados não correspondem aos originais"
            )
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_buffer_survives_process_restart(self):
        """
        PROPERTY: Buffer persiste entre reinicializações do processo
        
        Dados buffered devem sobreviver ao reinício do agente,
        garantindo que nenhum dado é perdido durante offline.
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # FASE 1: Primeira instância do buffer manager
            buffer1 = BufferManager(
                db_path="persistent_buffer.db",
                max_size_mb=10,
                config_dir=Path(temp_dir)
            )
            
            # Buffer alguns dados
            test_data = [
                {'timestamp': 1000000000.0, 'rssi_normalized': 0.5},
                {'timestamp': 1000000001.0, 'rssi_normalized': 0.6},
                {'timestamp': 1000000002.0, 'rssi_normalized': 0.7}
            ]
            
            for features in test_data:
                buffer1.add_data(features)
            
            # Verifica que dados foram salvos
            count1 = buffer1.get_pending_count()
            assert count1 == 3
            
            # Simula reinício do processo (cria nova instância)
            del buffer1
            
            # FASE 2: Segunda instância do buffer manager (mesmo arquivo)
            buffer2 = BufferManager(
                db_path="persistent_buffer.db",
                max_size_mb=10,
                config_dir=Path(temp_dir)
            )
            
            # PROPRIEDADE: Dados devem estar disponíveis após reinício
            count2 = buffer2.get_pending_count()
            assert count2 == 3, (
                f"Dados perdidos após reinício: esperado=3, atual={count2}"
            )
            
            # Verifica que dados são os mesmos
            recovered = buffer2.get_pending_data(limit=10)
            assert len(recovered) == 3
            
            for i, record in enumerate(recovered):
                assert record['timestamp'] == test_data[i]['timestamp']
                assert record['features']['rssi_normalized'] == test_data[i]['rssi_normalized']
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        buffer_size_mb=st.integers(min_value=5, max_value=10),
        payload_size_kb=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=10, deadline=None)
    def test_buffer_overflow_fifo_discard(self, buffer_size_mb, payload_size_kb):
        """
        Property 34: Buffer Overflow FIFO Discard
        Valida: Requisitos 31.6
        
        PROPERTY: Quando buffer atinge limite, dados mais antigos são descartados (FIFO)
        
        Quando o buffer local atinge o limite de tamanho configurado,
        novos dados devem substituir os dados mais antigos seguindo
        a política First In, First Out (FIFO).
        
        Isso garante que:
        1. O buffer nunca excede o limite de tamanho significativamente
        2. Dados mais recentes têm prioridade
        3. Dados mais antigos são descartados primeiro
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Cria buffer com tamanho limitado
            buffer_manager = BufferManager(
                db_path="overflow_test.db",
                max_size_mb=buffer_size_mb,
                config_dir=Path(temp_dir)
            )
            
            # Calcula quantos samples cabem no buffer
            # Cada sample tem aproximadamente payload_size_kb de tamanho
            samples_to_fill = int((buffer_size_mb * 1024) / payload_size_kb)
            
            # Adiciona 30% a mais para garantir overflow moderado
            total_samples = int(samples_to_fill * 1.3)
            
            # FASE 1: Adiciona dados até causar overflow
            all_timestamps = []
            for i in range(total_samples):
                timestamp = 1000000000.0 + i
                all_timestamps.append(timestamp)
                
                features = {
                    'timestamp': timestamp,
                    'rssi_normalized': 0.5 + (i % 10) * 0.01,
                    'signal_variance': 0.1,
                    'signal_energy': 0.2,
                    'rate_of_change': 0.05,
                    'instability_score': 0.3,
                    'metadata': {
                        'index': i,
                        'padding': 'x' * (payload_size_kb * 1024)  # Preenche com dados
                    }
                }
                
                buffer_manager.add_data(features)
            
            # FASE 2: Verifica comportamento FIFO
            size_after_overflow = buffer_manager.get_buffer_size_mb()
            
            # PROPRIEDADE 1: Buffer não deve exceder limite significativamente
            # Permitimos margem de 50% para overhead do SQLite
            max_allowed_size = buffer_size_mb * 1.5
            assert size_after_overflow <= max_allowed_size, (
                f"Buffer excedeu limite crítico: {size_after_overflow:.2f} MB > {max_allowed_size:.2f} MB. "
                f"Buffer deve descartar dados antigos quando cheio."
            )
            
            # Recupera todos os dados após overflow
            data_after_overflow = buffer_manager.get_pending_data(limit=total_samples)
            timestamps_after_overflow = [record['timestamp'] for record in data_after_overflow]
            
            # PROPRIEDADE 2: Nem todos os dados devem estar presentes (houve descarte)
            assert len(timestamps_after_overflow) < total_samples, (
                f"Nenhum dado foi descartado: {len(timestamps_after_overflow)} >= {total_samples}. "
                f"Buffer deveria ter descartado dados antigos ao atingir limite."
            )
            
            # PROPRIEDADE 3: Dados mais recentes devem estar mais presentes que antigos
            # Divide em 3 partes: antigos (primeiros 33%), meio (33-66%), recentes (últimos 33%)
            third = len(all_timestamps) // 3
            old_timestamps = all_timestamps[:third]
            recent_timestamps = all_timestamps[-third:]
            
            old_present = sum(1 for ts in old_timestamps if ts in timestamps_after_overflow)
            recent_present = sum(1 for ts in recent_timestamps if ts in timestamps_after_overflow)
            
            old_percentage = (old_present / len(old_timestamps)) * 100 if old_timestamps else 0
            recent_percentage = (recent_present / len(recent_timestamps)) * 100 if recent_timestamps else 0
            
            # Dados recentes devem ter maior taxa de presença que dados antigos
            assert recent_percentage > old_percentage, (
                f"FIFO não está funcionando: dados recentes ({recent_percentage:.1f}%) não são mais preservados que antigos ({old_percentage:.1f}%). "
                f"FIFO deve preservar dados mais recentes."
            )
            
            # PROPRIEDADE 4: Dados devem permanecer em ordem cronológica
            for i in range(len(timestamps_after_overflow) - 1):
                assert timestamps_after_overflow[i] <= timestamps_after_overflow[i + 1], (
                    f"Ordem cronológica violada após FIFO no índice {i}: "
                    f"{timestamps_after_overflow[i]} > {timestamps_after_overflow[i + 1]}"
                )
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_buffer_100mb_limit_enforcement(self):
        """
        Property 34 (Specific): Buffer de 100 MB não deve ser excedido
        Valida: Requisitos 31.5, 31.6
        
        PROPERTY: Buffer com limite de 100 MB deve descartar dados antigos via FIFO
        
        Teste específico para o limite de 100 MB mencionado nos requisitos.
        Verifica que o buffer respeita o limite e descarta dados antigos
        quando necessário.
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Cria buffer com limite de 100 MB (como especificado nos requisitos)
            buffer_manager = BufferManager(
                db_path="buffer_100mb.db",
                max_size_mb=100,
                config_dir=Path(temp_dir)
            )
            
            # Adiciona dados até aproximar do limite
            # Cada sample tem ~10 KB (features + metadata)
            samples_to_add = 12000  # ~120 MB de dados (vai causar overflow)
            
            print(f"\n[Test] Adicionando {samples_to_add} samples ao buffer de 100 MB...")
            
            first_batch_timestamps = []
            second_batch_timestamps = []
            
            # Primeira metade dos dados (mais antigos)
            for i in range(samples_to_add // 2):
                timestamp = 1000000000.0 + i
                first_batch_timestamps.append(timestamp)
                
                features = {
                    'timestamp': timestamp,
                    'rssi_normalized': 0.5,
                    'signal_variance': 0.1,
                    'signal_energy': 0.2,
                    'rate_of_change': 0.05,
                    'instability_score': 0.3,
                    'metadata': {
                        'batch': 'first',
                        'padding': 'x' * 10000  # ~10 KB por sample
                    }
                }
                
                buffer_manager.add_data(features)
                
                # Log progresso a cada 1000 samples
                if (i + 1) % 1000 == 0:
                    size_mb = buffer_manager.get_buffer_size_mb()
                    print(f"  Progress: {i + 1} samples, buffer size: {size_mb:.2f} MB")
            
            # Segunda metade dos dados (mais recentes)
            for i in range(samples_to_add // 2):
                timestamp = 2000000000.0 + i
                second_batch_timestamps.append(timestamp)
                
                features = {
                    'timestamp': timestamp,
                    'rssi_normalized': 0.8,
                    'signal_variance': 0.2,
                    'signal_energy': 0.3,
                    'rate_of_change': 0.1,
                    'instability_score': 0.4,
                    'metadata': {
                        'batch': 'second',
                        'padding': 'y' * 10000  # ~10 KB por sample
                    }
                }
                
                buffer_manager.add_data(features)
                
                if (i + 1) % 1000 == 0:
                    size_mb = buffer_manager.get_buffer_size_mb()
                    print(f"  Progress: {samples_to_add // 2 + i + 1} samples, buffer size: {size_mb:.2f} MB")
            
            # Verifica tamanho final
            final_size_mb = buffer_manager.get_buffer_size_mb()
            print(f"\n[Test] Tamanho final do buffer: {final_size_mb:.2f} MB")
            
            # PROPRIEDADE 1: Buffer não deve exceder 150 MB (100 MB + 50% overhead SQLite)
            assert final_size_mb <= 150, (
                f"Buffer excedeu limite crítico: {final_size_mb:.2f} MB > 150 MB. "
                f"Buffer deve descartar dados antigos para manter limite de 100 MB."
            )
            
            # Recupera todos os dados do buffer
            buffered_data = buffer_manager.get_pending_data(limit=samples_to_add)
            recovered_timestamps = [record['timestamp'] for record in buffered_data]
            
            print(f"[Test] Dados recuperados: {len(buffered_data)} samples")
            
            # PROPRIEDADE 2: Dados da segunda batch (mais recentes) devem estar presentes
            second_batch_present = sum(1 for ts in second_batch_timestamps if ts in recovered_timestamps)
            second_batch_percentage = (second_batch_present / len(second_batch_timestamps)) * 100
            
            print(f"[Test] Segunda batch presente: {second_batch_percentage:.1f}%")
            
            assert second_batch_percentage >= 90, (
                f"Dados mais recentes foram descartados: apenas {second_batch_percentage:.1f}% presentes. "
                f"FIFO deve preservar dados mais recentes."
            )
            
            # PROPRIEDADE 3: Dados da primeira batch (mais antigos) devem ter sido descartados
            first_batch_present = sum(1 for ts in first_batch_timestamps if ts in recovered_timestamps)
            first_batch_percentage = (first_batch_present / len(first_batch_timestamps)) * 100
            
            print(f"[Test] Primeira batch presente: {first_batch_percentage:.1f}%")
            
            # Esperamos que a maioria dos dados antigos tenha sido descartada
            assert first_batch_percentage < 50, (
                f"Dados mais antigos não foram descartados: {first_batch_percentage:.1f}% ainda presentes. "
                f"FIFO deve descartar dados mais antigos primeiro quando buffer está cheio."
            )
            
            # PROPRIEDADE 4: Ordem cronológica deve ser mantida
            for i in range(len(recovered_timestamps) - 1):
                assert recovered_timestamps[i] <= recovered_timestamps[i + 1], (
                    f"Ordem cronológica violada após FIFO no índice {i}: "
                    f"{recovered_timestamps[i]} > {recovered_timestamps[i + 1]}"
                )
            
            print(f"[Test] ✓ FIFO funcionando corretamente: dados antigos descartados, recentes preservados")
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run_property_tests())
