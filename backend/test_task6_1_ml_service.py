"""
Testes para Tarefa 6.1 - MLService

Testa:
- start_data_collection() para ativar coleta
- label_event() para rotular eventos em tempo real
- export_dataset() para exportar CSV
- Metadados (timestamp, configuração, condições)
"""

import pytest
import tempfile
import csv
import json
from pathlib import Path
from unittest.mock import Mock

from app.services.ml_service import MLService, LabeledSample
from app.processing.signal_processor import ProcessedFeatures


@pytest.fixture
def temp_models_dir():
    """Cria diretório temporário para modelos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def ml_service(temp_models_dir):
    """Cria instância do MLService para testes."""
    # Reset singleton
    MLService._instance = None
    service = MLService(models_dir=temp_models_dir)
    return service


@pytest.fixture
def sample_features():
    """Cria features de exemplo para testes."""
    return ProcessedFeatures(
        timestamp=1234567890.0,
        rssi_normalized=50.0,
        rssi_smoothed=48.5,
        rate_of_change=1.2,
        signal_energy=100.0,
        signal_variance=3.0,
        csi_mean_amplitude=10.0,
        csi_std_amplitude=2.0,
        instability_score=0.5,
        raw_rssi=-45.0
    )


class TestMLServiceBasicFunctionality:
    """Testes de funcionalidade básica do MLService."""
    
    def test_initialization(self, ml_service, temp_models_dir):
        """Testa inicialização do serviço."""
        assert ml_service._models_dir == temp_models_dir
        assert ml_service._models_dir.exists()
        assert not ml_service.is_collecting
        assert ml_service.samples_count == 0
    
    def test_start_data_collection(self, ml_service):
        """Testa ativação da coleta de dados."""
        # Inicia coleta
        ml_service.start_data_collection()
        
        assert ml_service.is_collecting
        assert ml_service.samples_count == 0
        assert len(ml_service._pending_features) == 0
    
    def test_stop_data_collection(self, ml_service):
        """Testa parada da coleta de dados."""
        # Inicia e para coleta
        ml_service.start_data_collection()
        ml_service.stop_data_collection()
        
        assert not ml_service.is_collecting
    
    def test_add_features_when_not_collecting(self, ml_service, sample_features):
        """Testa que features não são adicionadas quando coleta está inativa."""
        ml_service.add_features(sample_features)
        
        assert len(ml_service._pending_features) == 0
    
    def test_add_features_when_collecting(self, ml_service, sample_features):
        """Testa adição de features durante coleta."""
        ml_service.start_data_collection()
        ml_service.add_features(sample_features)
        
        assert len(ml_service._pending_features) == 1
        assert ml_service._pending_features[0] == sample_features


class TestLabelEvent:
    """Testes de rotulação de eventos."""
    
    def test_label_event_basic(self, ml_service, sample_features):
        """Testa rotulação básica de evento."""
        ml_service.start_data_collection()
        
        # Adiciona features
        for i in range(5):
            ml_service.add_features(sample_features)
        
        # Rotula evento
        samples_created = ml_service.label_event("presence_moving", window_seconds=5)
        
        assert samples_created == 5
        assert ml_service.samples_count == 5
        
        # Verifica primeira amostra
        sample = ml_service._collected_samples[0]
        assert sample.label == "presence_moving"
        assert sample.rssi_normalized == sample_features.rssi_normalized
        assert sample.timestamp == sample_features.timestamp
    
    def test_label_event_with_metadata(self, ml_service, sample_features):
        """Testa rotulação com metadados."""
        ml_service.start_data_collection()
        ml_service.add_features(sample_features)
        
        system_config = {
            "movement_sensitivity": 2.0,
            "fall_threshold": 12.0
        }
        
        environmental_conditions = {
            "temperature": 22.5,
            "humidity": 45.0
        }
        
        samples_created = ml_service.label_event(
            "presence_still",
            window_seconds=1,
            system_config=system_config,
            environmental_conditions=environmental_conditions
        )
        
        assert samples_created == 1
        
        sample = ml_service._collected_samples[0]
        assert sample.system_config == system_config
        assert sample.environmental_conditions == environmental_conditions
    
    def test_label_event_invalid_label(self, ml_service, sample_features):
        """Testa rotulação com rótulo inválido."""
        ml_service.start_data_collection()
        ml_service.add_features(sample_features)
        
        samples_created = ml_service.label_event("invalid_label")
        
        assert samples_created == 0
        assert ml_service.samples_count == 0
    
    def test_label_event_when_not_collecting(self, ml_service, sample_features):
        """Testa que rotulação não funciona quando coleta está inativa."""
        ml_service.add_features(sample_features)
        
        samples_created = ml_service.label_event("presence_moving")
        
        assert samples_created == 0
    
    def test_label_event_window_larger_than_buffer(self, ml_service, sample_features):
        """Testa rotulação com janela maior que buffer disponível."""
        ml_service.start_data_collection()
        
        # Adiciona apenas 3 features
        for i in range(3):
            ml_service.add_features(sample_features)
        
        # Tenta rotular 10 segundos
        samples_created = ml_service.label_event("presence_moving", window_seconds=10)
        
        # Deve rotular apenas as 3 disponíveis
        assert samples_created == 3
    
    def test_label_event_no_features_available(self, ml_service):
        """Testa rotulação sem features disponíveis."""
        ml_service.start_data_collection()
        
        samples_created = ml_service.label_event("presence_moving")
        
        assert samples_created == 0
    
    def test_label_multiple_events(self, ml_service, sample_features):
        """Testa rotulação de múltiplos eventos."""
        ml_service.start_data_collection()
        
        # Adiciona features e rotula primeiro evento
        for i in range(5):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=5)
        
        # Adiciona mais features e rotula segundo evento
        for i in range(3):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_still", window_seconds=3)
        
        assert ml_service.samples_count == 8
        
        # Verifica rótulos
        assert ml_service._collected_samples[0].label == "presence_moving"
        assert ml_service._collected_samples[5].label == "presence_still"


class TestExportDataset:
    """Testes de exportação de dataset."""
    
    @pytest.mark.asyncio
    async def test_export_dataset_basic(self, ml_service, sample_features, temp_models_dir):
        """Testa exportação básica de dataset."""
        ml_service.start_data_collection()
        
        # Coleta algumas amostras
        for i in range(5):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=5)
        
        # Exporta dataset
        output_path = await ml_service.export_dataset("test_dataset.csv")
        
        assert output_path.exists()
        assert output_path.name == "test_dataset.csv"
        assert output_path.parent == temp_models_dir
    
    @pytest.mark.asyncio
    async def test_export_dataset_csv_content(self, ml_service, sample_features, temp_models_dir):
        """Testa conteúdo do CSV exportado."""
        ml_service.start_data_collection()
        
        # Coleta amostras
        for i in range(3):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_still", window_seconds=3)
        
        # Exporta
        output_path = await ml_service.export_dataset("test.csv")
        
        # Lê CSV
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        
        # Verifica primeira linha
        row = rows[0]
        assert row['label'] == 'presence_still'
        assert float(row['rssi_normalized']) == sample_features.rssi_normalized
        assert float(row['signal_variance']) == sample_features.signal_variance
    
    @pytest.mark.asyncio
    async def test_export_dataset_with_metadata(self, ml_service, sample_features):
        """Testa exportação com metadados."""
        ml_service.start_data_collection()
        
        ml_service.add_features(sample_features)
        ml_service.label_event(
            "presence_moving",
            window_seconds=1,
            system_config={"sensitivity": 2.0},
            environmental_conditions={"temp": 22.0}
        )
        
        # Exporta com metadados
        output_path = await ml_service.export_dataset("test_meta.csv", include_metadata=True)
        
        # Lê CSV
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        row = rows[0]
        assert 'system_config' in row
        assert 'environmental_conditions' in row
        
        # Verifica que metadados são JSON válidos
        config = json.loads(row['system_config'])
        conditions = json.loads(row['environmental_conditions'])
        
        assert config == {"sensitivity": 2.0}
        assert conditions == {"temp": 22.0}
    
    @pytest.mark.asyncio
    async def test_export_dataset_without_metadata(self, ml_service, sample_features):
        """Testa exportação sem metadados."""
        ml_service.start_data_collection()
        
        ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=1)
        
        # Exporta sem metadados
        output_path = await ml_service.export_dataset("test_no_meta.csv", include_metadata=False)
        
        # Lê CSV
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        
        assert 'system_config' not in fieldnames
        assert 'environmental_conditions' not in fieldnames
    
    @pytest.mark.asyncio
    async def test_export_dataset_no_samples(self, ml_service):
        """Testa exportação sem amostras coletadas."""
        with pytest.raises(ValueError, match="Nenhuma amostra coletada"):
            await ml_service.export_dataset("empty.csv")
    
    @pytest.mark.asyncio
    async def test_export_dataset_adds_csv_extension(self, ml_service, sample_features):
        """Testa que extensão .csv é adicionada automaticamente."""
        ml_service.start_data_collection()
        ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=1)
        
        output_path = await ml_service.export_dataset("test_dataset")
        
        assert output_path.name == "test_dataset.csv"


class TestUtilityMethods:
    """Testes de métodos utilitários."""
    
    def test_get_label_distribution(self, ml_service, sample_features):
        """Testa distribuição de rótulos."""
        ml_service.start_data_collection()
        
        # Adiciona amostras com diferentes rótulos
        for i in range(5):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=5)
        
        for i in range(3):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_still", window_seconds=3)
        
        distribution = ml_service.get_label_distribution()
        
        assert distribution["presence_moving"] == 5
        assert distribution["presence_still"] == 3
    
    def test_clear_samples(self, ml_service, sample_features):
        """Testa limpeza de amostras."""
        ml_service.start_data_collection()
        
        for i in range(5):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=5)
        
        assert ml_service.samples_count == 5
        
        ml_service.clear_samples()
        
        assert ml_service.samples_count == 0
        assert len(ml_service._pending_features) == 0
    
    def test_get_collection_stats(self, ml_service, sample_features):
        """Testa estatísticas de coleta."""
        ml_service.start_data_collection()
        
        for i in range(3):
            ml_service.add_features(sample_features)
        ml_service.label_event("presence_moving", window_seconds=3)
        
        stats = ml_service.get_collection_stats()
        
        assert stats["is_collecting"] == True
        assert stats["total_samples"] == 3
        assert stats["pending_features"] == 3
        assert "label_distribution" in stats
        assert "first_sample_timestamp" in stats
        assert "last_sample_timestamp" in stats
        assert "collection_duration_seconds" in stats


class TestBufferManagement:
    """Testes de gerenciamento de buffer."""
    
    def test_pending_features_buffer_limit(self, ml_service, sample_features):
        """Testa que buffer de features tem limite."""
        ml_service.start_data_collection()
        
        # Adiciona mais features que o limite do buffer
        for i in range(15):
            ml_service.add_features(sample_features)
        
        # Buffer deve ter no máximo 10 features
        assert len(ml_service._pending_features) == 10
    
    def test_buffer_is_circular(self, ml_service):
        """Testa que buffer é circular (FIFO)."""
        ml_service.start_data_collection()
        
        # Adiciona features com timestamps diferentes
        for i in range(15):
            features = ProcessedFeatures(
                timestamp=float(i),
                rssi_normalized=50.0,
                rssi_smoothed=48.5,
                rate_of_change=1.2,
                signal_energy=100.0,
                signal_variance=3.0,
                csi_mean_amplitude=10.0,
                csi_std_amplitude=2.0,
                instability_score=0.5,
                raw_rssi=-45.0
            )
            ml_service.add_features(features)
        
        # Primeiras features devem ter sido removidas
        # Buffer deve conter features 5-14
        assert ml_service._pending_features[0].timestamp == 5.0
        assert ml_service._pending_features[-1].timestamp == 14.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
