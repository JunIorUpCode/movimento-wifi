"""
MLService - Serviço de Machine Learning para coleta e treinamento de dados.

Implementa:
- Coleta de dados rotulados para treinamento
- Rotulação de eventos em tempo real
- Exportação de datasets em formato CSV
- Metadados (timestamp, configuração, condições)

Requisitos: 7.1, 7.2, 7.3, 7.5
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.logging.structured_logger import get_logger
from app.processing.signal_processor import ProcessedFeatures


logger = get_logger(__name__)


@dataclass
class LabeledSample:
    """Amostra de dados rotulada para treinamento."""
    
    # Timestamp
    timestamp: float
    
    # Features RSSI
    rssi_normalized: float
    rssi_smoothed: float
    rate_of_change: float
    
    # Features de sinal
    signal_energy: float
    signal_variance: float
    csi_mean_amplitude: float
    csi_std_amplitude: float
    
    # Features temporais
    instability_score: float
    
    # RSSI bruto
    raw_rssi: float
    
    # Rótulo
    label: str
    
    # Metadados adicionais
    system_config: Dict[str, Any]
    environmental_conditions: Dict[str, Any]


class MLService:
    """Serviço de Machine Learning para coleta e treinamento de dados."""
    
    _instance: Optional[MLService] = None
    
    def __new__(cls, models_dir: Optional[Path] = None) -> MLService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, models_dir: Optional[Path] = None) -> None:
        if self._initialized:
            return
        self._initialized = True
        
        self._models_dir = models_dir or Path("models")
        self._models_dir.mkdir(exist_ok=True)
        
        self._data_collection_active = False
        self._collected_samples: List[LabeledSample] = []
        self._pending_features: List[ProcessedFeatures] = []
        self._max_pending_window = 10  # Mantém últimos 10 segundos
        
        logger.info(
            "MLService initialized",
            models_dir=str(self._models_dir)
        )
    
    @property
    def is_collecting(self) -> bool:
        """Retorna True se coleta de dados está ativa."""
        return self._data_collection_active
    
    @property
    def samples_count(self) -> int:
        """Retorna número de amostras coletadas."""
        return len(self._collected_samples)
    
    def start_data_collection(self) -> None:
        """
        Inicia coleta de dados para treinamento.
        
        Ativa o modo de coleta onde todas as features processadas
        são armazenadas em buffer para posterior rotulação.
        
        Implementa Requisito 7.1: Ativar modo de coleta
        """
        self._data_collection_active = True
        self._collected_samples.clear()
        self._pending_features.clear()
        
        logger.info(
            "Data collection started",
            mode="active"
        )
    
    def stop_data_collection(self) -> None:
        """
        Para coleta de dados.
        
        Desativa o modo de coleta mas mantém as amostras já coletadas
        para exportação posterior.
        """
        self._data_collection_active = False
        
        logger.info(
            "Data collection stopped",
            samples_collected=len(self._collected_samples),
            pending_features=len(self._pending_features)
        )
    
    def add_features(self, features: ProcessedFeatures) -> None:
        """
        Adiciona features ao buffer para posterior rotulação.
        
        Mantém um buffer circular com as últimas features processadas
        para permitir rotulação retroativa de eventos.
        
        Args:
            features: Features processadas do sinal
        """
        if not self._data_collection_active:
            return
        
        self._pending_features.append(features)
        
        # Mantém apenas últimos N segundos
        if len(self._pending_features) > self._max_pending_window:
            self._pending_features.pop(0)
    
    def label_event(
        self,
        label: str,
        window_seconds: int = 10,
        system_config: Optional[Dict[str, Any]] = None,
        environmental_conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Rotula evento em tempo real.
        
        Associa um rótulo às features dos últimos N segundos,
        criando amostras rotuladas para o dataset de treinamento.
        
        Implementa Requisito 7.2: Rotular eventos em tempo real
        Implementa Requisito 7.5: Incluir metadados
        
        Args:
            label: Rótulo do evento (ex: "presence_still", "presence_moving", "fall_suspected", "no_presence")
            window_seconds: Janela de tempo em segundos para rotular (padrão: 10)
            system_config: Configuração do sistema no momento da rotulação
            environmental_conditions: Condições ambientais (temperatura, umidade, etc.)
        
        Returns:
            Número de amostras rotuladas
        """
        if not self._data_collection_active:
            logger.warning(
                "Cannot label event: data collection is not active",
                label=label
            )
            return 0
        
        # Valida rótulo
        valid_labels = [
            "no_presence",
            "presence_still",
            "presence_moving",
            "fall_suspected",
            "prolonged_inactivity"
        ]
        
        if label not in valid_labels:
            logger.error(
                "Invalid label provided",
                label=label,
                valid_labels=valid_labels
            )
            return 0
        
        # Determina quantas features rotular
        num_features = min(window_seconds, len(self._pending_features))
        
        if num_features == 0:
            logger.warning(
                "No features available to label",
                label=label,
                window_seconds=window_seconds
            )
            return 0
        
        # Pega features da janela
        features_to_label = self._pending_features[-num_features:]
        
        # Prepara metadados
        config = system_config or {}
        conditions = environmental_conditions or {}
        
        # Cria amostras rotuladas
        samples_created = 0
        for features in features_to_label:
            sample = LabeledSample(
                timestamp=features.timestamp,
                rssi_normalized=features.rssi_normalized,
                rssi_smoothed=features.rssi_smoothed,
                rate_of_change=features.rate_of_change,
                signal_energy=features.signal_energy,
                signal_variance=features.signal_variance,
                csi_mean_amplitude=features.csi_mean_amplitude,
                csi_std_amplitude=features.csi_std_amplitude,
                instability_score=features.instability_score,
                raw_rssi=features.raw_rssi,
                label=label,
                system_config=config,
                environmental_conditions=conditions
            )
            
            self._collected_samples.append(sample)
            samples_created += 1
        
        logger.info(
            "Event labeled",
            label=label,
            samples_created=samples_created,
            window_seconds=window_seconds,
            total_samples=len(self._collected_samples)
        )
        
        return samples_created
    
    async def export_dataset(
        self,
        filename: str,
        include_metadata: bool = True
    ) -> Path:
        """
        Exporta dataset coletado para CSV.
        
        Gera arquivo CSV com todas as amostras rotuladas,
        compatível com scikit-learn e PyTorch.
        
        Implementa Requisito 7.3: Exportar CSV
        Implementa Requisito 7.5: Incluir metadados
        
        Args:
            filename: Nome do arquivo CSV (ex: "training_data.csv")
            include_metadata: Se True, inclui colunas de metadados
        
        Returns:
            Path do arquivo exportado
        
        Raises:
            ValueError: Se não houver amostras para exportar
        """
        if not self._collected_samples:
            raise ValueError("Nenhuma amostra coletada para exportar")
        
        # Garante extensão .csv
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        output_path = self._models_dir / filename
        
        # Define colunas do CSV
        fieldnames = [
            'timestamp',
            'rssi_normalized',
            'rssi_smoothed',
            'rate_of_change',
            'signal_energy',
            'signal_variance',
            'csi_mean_amplitude',
            'csi_std_amplitude',
            'instability_score',
            'raw_rssi',
            'label'
        ]
        
        if include_metadata:
            fieldnames.extend([
                'system_config',
                'environmental_conditions'
            ])
        
        # Escreve CSV
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for sample in self._collected_samples:
                    row = {
                        'timestamp': sample.timestamp,
                        'rssi_normalized': sample.rssi_normalized,
                        'rssi_smoothed': sample.rssi_smoothed,
                        'rate_of_change': sample.rate_of_change,
                        'signal_energy': sample.signal_energy,
                        'signal_variance': sample.signal_variance,
                        'csi_mean_amplitude': sample.csi_mean_amplitude,
                        'csi_std_amplitude': sample.csi_std_amplitude,
                        'instability_score': sample.instability_score,
                        'raw_rssi': sample.raw_rssi,
                        'label': sample.label
                    }
                    
                    if include_metadata:
                        # Serializa metadados como string JSON
                        import json
                        row['system_config'] = json.dumps(sample.system_config)
                        row['environmental_conditions'] = json.dumps(sample.environmental_conditions)
                    
                    writer.writerow(row)
            
            logger.info(
                "Dataset exported successfully",
                filename=filename,
                path=str(output_path),
                samples_count=len(self._collected_samples),
                include_metadata=include_metadata
            )
            
            return output_path
            
        except Exception as e:
            logger.error(
                "Failed to export dataset",
                filename=filename,
                error=str(e)
            )
            raise
    
    def get_label_distribution(self) -> Dict[str, int]:
        """
        Retorna distribuição de rótulos no dataset coletado.
        
        Returns:
            Dicionário com contagem de cada rótulo
        """
        distribution: Dict[str, int] = {}
        
        for sample in self._collected_samples:
            label = sample.label
            distribution[label] = distribution.get(label, 0) + 1
        
        return distribution
    
    def clear_samples(self) -> None:
        """
        Limpa todas as amostras coletadas.
        
        Use com cuidado - esta operação não pode ser desfeita.
        """
        samples_count = len(self._collected_samples)
        self._collected_samples.clear()
        self._pending_features.clear()
        
        logger.info(
            "Samples cleared",
            samples_removed=samples_count
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da coleta de dados.
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            "is_collecting": self._data_collection_active,
            "total_samples": len(self._collected_samples),
            "pending_features": len(self._pending_features),
            "label_distribution": self.get_label_distribution(),
            "models_dir": str(self._models_dir)
        }
        
        if self._collected_samples:
            stats["first_sample_timestamp"] = self._collected_samples[0].timestamp
            stats["last_sample_timestamp"] = self._collected_samples[-1].timestamp
            stats["collection_duration_seconds"] = (
                self._collected_samples[-1].timestamp - 
                self._collected_samples[0].timestamp
            )
        
        return stats


# Instância global
ml_service = MLService()
