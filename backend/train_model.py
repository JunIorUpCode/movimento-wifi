"""
Script de Treinamento de Modelo ML - WiFiSense

Este script treina um modelo RandomForestClassifier usando dados coletados
pelo MLService. O modelo é usado pelo MLDetector para classificação de eventos.

Implementa Tarefa 7.1:
- Carregamento de dataset CSV
- Extração de features (18 dimensões)
- Split treino/teste
- Normalização com StandardScaler
- Treinamento com RandomForestClassifier
- Salvamento de modelo e scaler em formato .pkl

Requisitos: 8.4, 8.5
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib


def load_dataset(csv_path: Path) -> pd.DataFrame:
    """
    Carrega dataset CSV exportado pelo MLService.
    
    Args:
        csv_path: Caminho para o arquivo CSV
    
    Returns:
        DataFrame com os dados carregados
    
    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se o CSV estiver malformado
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Dataset carregado: {len(df)} amostras")
        return df
    except Exception as e:
        raise ValueError(f"Erro ao carregar CSV: {e}")


def extract_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extrai features e labels do dataset.
    
    O MLService exporta 9 features básicas por amostra. Para criar
    features de janela (18 dimensões), calculamos estatísticas sobre
    grupos de amostras consecutivas.
    
    Features extraídas (18 dimensões):
    - 9 features básicas (média da janela)
    - 9 features de variabilidade (desvio padrão da janela)
    
    Args:
        df: DataFrame com dados brutos
    
    Returns:
        Tuple (X, y) onde:
        - X: array (n_samples, 18) com features
        - y: array (n_samples,) com labels
    """
    # Features básicas exportadas pelo MLService
    feature_columns = [
        'rssi_normalized',
        'rssi_smoothed',
        'rate_of_change',
        'signal_energy',
        'signal_variance',
        'csi_mean_amplitude',
        'csi_std_amplitude',
        'instability_score',
        'raw_rssi'
    ]
    
    # Valida que todas as colunas existem
    missing_cols = set(feature_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Colunas faltando no dataset: {missing_cols}")
    
    if 'label' not in df.columns:
        raise ValueError("Coluna 'label' não encontrada no dataset")
    
    # Extrai features básicas
    X_basic = df[feature_columns].values
    y = df['label'].values
    
    # Cria features de janela (estatísticas sobre grupos de 10 amostras)
    window_size = 10
    X_windowed = []
    y_windowed = []
    
    for i in range(len(df) - window_size + 1):
        window = X_basic[i:i+window_size]
        
        # Calcula média e desvio padrão da janela
        window_mean = np.mean(window, axis=0)  # 9 features
        window_std = np.std(window, axis=0)    # 9 features
        
        # Concatena para formar 18 features
        features_18d = np.concatenate([window_mean, window_std])
        
        X_windowed.append(features_18d)
        # Usa o label da última amostra da janela
        y_windowed.append(y[i + window_size - 1])
    
    X = np.array(X_windowed)
    y = np.array(y_windowed)
    
    print(f"✓ Features extraídas: {X.shape[0]} amostras, {X.shape[1]} dimensões")
    print(f"  Distribuição de labels:")
    unique, counts = np.unique(y, return_counts=True)
    for label, count in zip(unique, counts):
        print(f"    {label}: {count} ({count/len(y)*100:.1f}%)")
    
    return X, y


def split_data(X: np.ndarray, y: np.ndarray, 
               test_size: float = 0.2, 
               random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Divide dados em conjuntos de treino e teste.
    
    Args:
        X: Features
        y: Labels
        test_size: Proporção do conjunto de teste (padrão: 0.2)
        random_state: Seed para reprodutibilidade
    
    Returns:
        Tuple (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y  # Mantém proporção de classes
    )
    
    print(f"✓ Dados divididos:")
    print(f"  Treino: {len(X_train)} amostras")
    print(f"  Teste: {len(X_test)} amostras")
    
    return X_train, X_test, y_train, y_test


def normalize_features(X_train: np.ndarray, 
                       X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Normaliza features usando StandardScaler.
    
    Importante: O scaler é ajustado apenas nos dados de treino
    para evitar data leakage.
    
    Args:
        X_train: Features de treino
        X_test: Features de teste
    
    Returns:
        Tuple (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()
    
    # Ajusta scaler apenas no treino
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Aplica transformação no teste
    X_test_scaled = scaler.transform(X_test)
    
    print(f"✓ Features normalizadas com StandardScaler")
    print(f"  Média das features de treino: {X_train_scaled.mean(axis=0)[:3]} ...")
    print(f"  Desvio padrão das features de treino: {X_train_scaled.std(axis=0)[:3]} ...")
    
    return X_train_scaled, X_test_scaled, scaler


def train_model(X_train: np.ndarray, 
                y_train: np.ndarray,
                n_estimators: int = 100,
                max_depth: int = 20,
                random_state: int = 42) -> RandomForestClassifier:
    """
    Treina modelo RandomForestClassifier.
    
    Args:
        X_train: Features de treino normalizadas
        y_train: Labels de treino
        n_estimators: Número de árvores na floresta
        max_depth: Profundidade máxima das árvores
        random_state: Seed para reprodutibilidade
    
    Returns:
        Modelo treinado
    """
    print(f"\n🌲 Treinando RandomForestClassifier...")
    print(f"  n_estimators: {n_estimators}")
    print(f"  max_depth: {max_depth}")
    
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,  # Usa todos os cores disponíveis
        verbose=1
    )
    
    model.fit(X_train, y_train)
    
    print(f"✓ Modelo treinado com sucesso")
    
    return model


def evaluate_model(model: RandomForestClassifier,
                   X_test: np.ndarray,
                   y_test: np.ndarray) -> Dict[str, Any]:
    """
    Avalia modelo no conjunto de teste.
    
    Args:
        model: Modelo treinado
        X_test: Features de teste normalizadas
        y_test: Labels de teste
    
    Returns:
        Dicionário com métricas de avaliação
    """
    print(f"\n📊 Avaliando modelo...")
    
    # Predições
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Métricas
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✓ Acurácia: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"\nRelatório de Classificação:")
    print(classification_report(y_test, y_pred))
    
    print(f"\nMatriz de Confusão:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    feature_names = [
        'rssi_norm_mean', 'rssi_smooth_mean', 'roc_mean', 'energy_mean', 
        'variance_mean', 'csi_mean_mean', 'csi_std_mean', 'instability_mean', 'raw_rssi_mean',
        'rssi_norm_std', 'rssi_smooth_std', 'roc_std', 'energy_std',
        'variance_std', 'csi_mean_std', 'csi_std_std', 'instability_std', 'raw_rssi_std'
    ]
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print(f"\nTop 10 Features Mais Importantes:")
    for i in range(min(10, len(feature_names))):
        idx = indices[i]
        print(f"  {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")
    
    return {
        'accuracy': accuracy,
        'classification_report': classification_report(y_test, y_pred, output_dict=True),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'feature_importances': {
            name: float(imp) 
            for name, imp in zip(feature_names, importances)
        }
    }


def save_model(model: RandomForestClassifier,
               scaler: StandardScaler,
               metrics: Dict[str, Any],
               output_dir: Path,
               model_name: str = "classifier") -> Tuple[Path, Path]:
    """
    Salva modelo e scaler em formato .pkl.
    
    Args:
        model: Modelo treinado
        scaler: Scaler ajustado
        metrics: Métricas de avaliação
        output_dir: Diretório de saída
        model_name: Nome base para os arquivos
    
    Returns:
        Tuple (model_path, scaler_path)
    """
    output_dir.mkdir(exist_ok=True)
    
    # Caminhos dos arquivos
    model_path = output_dir / f"{model_name}.pkl"
    scaler_path = output_dir / f"{model_name}_scaler.pkl"
    metadata_path = output_dir / f"{model_name}_metadata.json"
    
    # Salva modelo
    joblib.dump(model, model_path)
    print(f"✓ Modelo salvo: {model_path}")
    
    # Salva scaler
    joblib.dump(scaler, scaler_path)
    print(f"✓ Scaler salvo: {scaler_path}")
    
    # Salva metadados
    metadata = {
        'model_name': model_name,
        'model_type': 'RandomForestClassifier',
        'n_estimators': model.n_estimators,
        'max_depth': model.max_depth,
        'n_features': model.n_features_in_,
        'n_classes': len(model.classes_),
        'classes': model.classes_.tolist(),
        'accuracy': metrics['accuracy'],
        'feature_importances': metrics['feature_importances'],
        'trained_at': datetime.now().isoformat(),
        'training_samples': len(model.classes_)  # Placeholder
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadados salvos: {metadata_path}")
    
    return model_path, scaler_path


def main():
    """Função principal do script de treinamento."""
    parser = argparse.ArgumentParser(
        description='Treina modelo ML para WiFiSense',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python train_model.py dataset.csv
  python train_model.py dataset.csv --test-size 0.3
  python train_model.py dataset.csv --n-estimators 200 --max-depth 30
  python train_model.py dataset.csv --output-dir ./custom_models
        """
    )
    
    parser.add_argument(
        'dataset',
        type=str,
        help='Caminho para o arquivo CSV com dados de treinamento'
    )
    
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proporção do conjunto de teste (padrão: 0.2)'
    )
    
    parser.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Número de árvores na floresta (padrão: 100)'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=20,
        help='Profundidade máxima das árvores (padrão: 20)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models',
        help='Diretório de saída para modelo e scaler (padrão: models)'
    )
    
    parser.add_argument(
        '--model-name',
        type=str,
        default='classifier',
        help='Nome base para os arquivos de saída (padrão: classifier)'
    )
    
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Seed para reprodutibilidade (padrão: 42)'
    )
    
    args = parser.parse_args()
    
    try:
        print("=" * 70)
        print("🤖 WiFiSense - Treinamento de Modelo ML")
        print("=" * 70)
        print()
        
        # 1. Carrega dataset
        dataset_path = Path(args.dataset)
        df = load_dataset(dataset_path)
        print()
        
        # 2. Extrai features (18 dimensões)
        X, y = extract_features(df)
        print()
        
        # 3. Divide dados
        X_train, X_test, y_train, y_test = split_data(
            X, y, 
            test_size=args.test_size,
            random_state=args.random_state
        )
        print()
        
        # 4. Normaliza features
        X_train_scaled, X_test_scaled, scaler = normalize_features(X_train, X_test)
        
        # 5. Treina modelo
        model = train_model(
            X_train_scaled, 
            y_train,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            random_state=args.random_state
        )
        
        # 6. Avalia modelo
        metrics = evaluate_model(model, X_test_scaled, y_test)
        
        # 7. Salva modelo e scaler
        print()
        output_dir = Path(args.output_dir)
        model_path, scaler_path = save_model(
            model, 
            scaler, 
            metrics,
            output_dir,
            args.model_name
        )
        
        print()
        print("=" * 70)
        print("✅ Treinamento concluído com sucesso!")
        print("=" * 70)
        print(f"\nArquivos gerados:")
        print(f"  - Modelo: {model_path}")
        print(f"  - Scaler: {scaler_path}")
        print(f"  - Metadados: {output_dir / f'{args.model_name}_metadata.json'}")
        print(f"\nAcurácia final: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro durante treinamento: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
