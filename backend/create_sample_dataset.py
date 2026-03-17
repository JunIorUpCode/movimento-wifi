"""
Script para criar dataset de exemplo para treinamento ML.

Gera dados sintéticos com diferentes padrões de comportamento.
"""

import csv
import random
from pathlib import Path


def generate_sample_data(num_samples: int = 500) -> list[dict]:
    """Gera dados de exemplo para cada classe."""
    samples = []
    
    # Classe: no_presence (sem presença)
    for _ in range(num_samples // 5):
        samples.append({
            'timestamp': random.uniform(1000000, 2000000),
            'rssi_normalized': random.uniform(0.0, 0.2),
            'rssi_smoothed': random.uniform(-80, -70),
            'rate_of_change': random.uniform(-0.5, 0.5),
            'signal_energy': random.uniform(0, 5),
            'signal_variance': random.uniform(0, 1),
            'csi_mean_amplitude': random.uniform(0, 3),
            'csi_std_amplitude': random.uniform(0, 1),
            'instability_score': random.uniform(0, 0.2),
            'raw_rssi': random.uniform(-80, -70),
            'label': 'no_presence'
        })
    
    # Classe: presence_still (presença parada)
    for _ in range(num_samples // 5):
        samples.append({
            'timestamp': random.uniform(1000000, 2000000),
            'rssi_normalized': random.uniform(0.3, 0.5),
            'rssi_smoothed': random.uniform(-60, -50),
            'rate_of_change': random.uniform(-1, 1),
            'signal_energy': random.uniform(5, 15),
            'signal_variance': random.uniform(1, 3),
            'csi_mean_amplitude': random.uniform(3, 8),
            'csi_std_amplitude': random.uniform(1, 2),
            'instability_score': random.uniform(0.1, 0.3),
            'raw_rssi': random.uniform(-60, -50),
            'label': 'presence_still'
        })
    
    # Classe: presence_moving (presença em movimento)
    for _ in range(num_samples // 5):
        samples.append({
            'timestamp': random.uniform(1000000, 2000000),
            'rssi_normalized': random.uniform(0.5, 0.8),
            'rssi_smoothed': random.uniform(-50, -40),
            'rate_of_change': random.uniform(2, 8),
            'signal_energy': random.uniform(15, 30),
            'signal_variance': random.uniform(3, 8),
            'csi_mean_amplitude': random.uniform(8, 15),
            'csi_std_amplitude': random.uniform(2, 5),
            'instability_score': random.uniform(0.4, 0.7),
            'raw_rssi': random.uniform(-50, -40),
            'label': 'presence_moving'
        })
    
    # Classe: fall_suspected (queda suspeita)
    for _ in range(num_samples // 5):
        samples.append({
            'timestamp': random.uniform(1000000, 2000000),
            'rssi_normalized': random.uniform(0.7, 1.0),
            'rssi_smoothed': random.uniform(-40, -30),
            'rate_of_change': random.uniform(10, 20),
            'signal_energy': random.uniform(30, 50),
            'signal_variance': random.uniform(8, 15),
            'csi_mean_amplitude': random.uniform(15, 25),
            'csi_std_amplitude': random.uniform(5, 10),
            'instability_score': random.uniform(0.7, 1.0),
            'raw_rssi': random.uniform(-40, -30),
            'label': 'fall_suspected'
        })
    
    # Classe: prolonged_inactivity (inatividade prolongada)
    for _ in range(num_samples // 5):
        samples.append({
            'timestamp': random.uniform(1000000, 2000000),
            'rssi_normalized': random.uniform(0.2, 0.4),
            'rssi_smoothed': random.uniform(-65, -55),
            'rate_of_change': random.uniform(-0.5, 0.5),
            'signal_energy': random.uniform(3, 10),
            'signal_variance': random.uniform(0.5, 2),
            'csi_mean_amplitude': random.uniform(2, 6),
            'csi_std_amplitude': random.uniform(0.5, 1.5),
            'instability_score': random.uniform(0.1, 0.25),
            'raw_rssi': random.uniform(-65, -55),
            'label': 'prolonged_inactivity'
        })
    
    # Embaralha amostras
    random.shuffle(samples)
    
    return samples


def save_dataset(samples: list[dict], output_path: Path):
    """Salva dataset em CSV."""
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
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)
    
    print(f"✓ Dataset salvo: {output_path}")
    print(f"  Total de amostras: {len(samples)}")
    
    # Mostra distribuição de classes
    from collections import Counter
    label_counts = Counter(s['label'] for s in samples)
    print(f"  Distribuição de classes:")
    for label, count in sorted(label_counts.items()):
        print(f"    {label}: {count} ({count/len(samples)*100:.1f}%)")


if __name__ == "__main__":
    print("=" * 70)
    print("Criando Dataset de Exemplo para Treinamento ML")
    print("=" * 70)
    print()
    
    # Gera dados
    print("Gerando dados sintéticos...")
    samples = generate_sample_data(num_samples=500)
    
    # Salva dataset
    output_path = Path("models/sample_training_data.csv")
    output_path.parent.mkdir(exist_ok=True)
    
    save_dataset(samples, output_path)
    
    print()
    print("=" * 70)
    print("Dataset criado com sucesso!")
    print("=" * 70)
    print()
    print("Próximo passo: treinar modelo com:")
    print(f"  python backend/train_model.py {output_path}")
