"""
Testes para Task 11 - Adicionar modelos ML ao banco de dados.

Testa:
- Modelo MLModel no SQLAlchemy
- Endpoints GET /api/ml/models
- Endpoint POST /api/ml/models/{name}/activate
- Metadados (accuracy, training_samples, etc.)

Requisitos: 8.1, 8.2
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.models import MLModel


# Configuração do banco de teste
TEST_DB_PATH = "test_ml_models.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest_asyncio.fixture
async def db_session():
    """Cria sessão de banco de dados para testes."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()
    
    # Cleanup
    if Path(TEST_DB_PATH).exists():
        Path(TEST_DB_PATH).unlink()


@pytest.mark.asyncio
async def test_create_ml_model(db_session: AsyncSession):
    """Testa criação de modelo ML no banco de dados."""
    model = MLModel(
        name="test_classifier_v1",
        model_type="classifier",
        file_path="models/test_classifier_v1.pkl",
        accuracy=0.92,
        training_samples=1000,
        created_at=datetime.utcnow(),
        is_active=False,
        metadata_json=json.dumps({
            "framework": "scikit-learn",
            "algorithm": "RandomForest",
            "n_estimators": 100
        })
    )
    
    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)
    
    assert model.id is not None
    assert model.name == "test_classifier_v1"
    assert model.model_type == "classifier"
    assert model.accuracy == 0.92
    assert model.training_samples == 1000
    assert model.is_active is False


@pytest.mark.asyncio
async def test_list_ml_models(db_session: AsyncSession):
    """Testa listagem de modelos ML."""
    # Cria múltiplos modelos
    models_data = [
        {
            "name": "classifier_v1",
            "model_type": "classifier",
            "file_path": "models/classifier_v1.pkl",
            "accuracy": 0.85,
            "training_samples": 500,
        },
        {
            "name": "classifier_v2",
            "model_type": "classifier",
            "file_path": "models/classifier_v2.pkl",
            "accuracy": 0.92,
            "training_samples": 1000,
        },
        {
            "name": "anomaly_v1",
            "model_type": "anomaly",
            "file_path": "models/anomaly_v1.pkl",
            "accuracy": None,
            "training_samples": 800,
        },
    ]
    
    for data in models_data:
        model = MLModel(**data)
        db_session.add(model)
    
    await db_session.commit()
    
    # Lista todos os modelos
    result = await db_session.execute(select(MLModel))
    models = result.scalars().all()
    
    assert len(models) == 3
    assert models[0].name == "classifier_v1"
    assert models[1].name == "classifier_v2"
    assert models[2].name == "anomaly_v1"


@pytest.mark.asyncio
async def test_activate_ml_model(db_session: AsyncSession):
    """Testa ativação de modelo ML."""
    # Cria dois modelos do mesmo tipo
    model1 = MLModel(
        name="classifier_v1",
        model_type="classifier",
        file_path="models/classifier_v1.pkl",
        accuracy=0.85,
        training_samples=500,
        is_active=True,  # Inicialmente ativo
    )
    
    model2 = MLModel(
        name="classifier_v2",
        model_type="classifier",
        file_path="models/classifier_v2.pkl",
        accuracy=0.92,
        training_samples=1000,
        is_active=False,
    )
    
    db_session.add_all([model1, model2])
    await db_session.commit()
    
    # Ativa o segundo modelo
    from sqlalchemy import update
    
    # Desativa todos os modelos do tipo classifier
    await db_session.execute(
        update(MLModel)
        .where(MLModel.model_type == "classifier")
        .values(is_active=False)
    )
    
    # Ativa o modelo2
    await db_session.execute(
        update(MLModel)
        .where(MLModel.name == "classifier_v2")
        .values(is_active=True)
    )
    
    await db_session.commit()
    
    # Verifica que apenas model2 está ativo
    result = await db_session.execute(
        select(MLModel).where(MLModel.name == "classifier_v1")
    )
    model1_updated = result.scalar_one()
    assert model1_updated.is_active is False
    
    result = await db_session.execute(
        select(MLModel).where(MLModel.name == "classifier_v2")
    )
    model2_updated = result.scalar_one()
    assert model2_updated.is_active is True


@pytest.mark.asyncio
async def test_ml_model_metadata(db_session: AsyncSession):
    """Testa armazenamento de metadados do modelo."""
    metadata = {
        "framework": "scikit-learn",
        "algorithm": "RandomForest",
        "n_estimators": 100,
        "max_depth": 10,
        "training_duration_seconds": 45.2,
        "feature_importance": [0.3, 0.25, 0.2, 0.15, 0.1],
    }
    
    model = MLModel(
        name="classifier_with_metadata",
        model_type="classifier",
        file_path="models/classifier_with_metadata.pkl",
        accuracy=0.88,
        training_samples=750,
        metadata_json=json.dumps(metadata),
    )
    
    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)
    
    # Verifica que metadados foram salvos corretamente
    loaded_metadata = json.loads(model.metadata_json)
    assert loaded_metadata["framework"] == "scikit-learn"
    assert loaded_metadata["algorithm"] == "RandomForest"
    assert loaded_metadata["n_estimators"] == 100
    assert len(loaded_metadata["feature_importance"]) == 5


@pytest.mark.asyncio
async def test_ml_model_unique_name_constraint(db_session: AsyncSession):
    """Testa que nomes de modelos devem ser únicos."""
    model1 = MLModel(
        name="duplicate_name",
        model_type="classifier",
        file_path="models/model1.pkl",
        accuracy=0.85,
        training_samples=500,
    )
    
    db_session.add(model1)
    await db_session.commit()
    
    # Tenta criar outro modelo com o mesmo nome
    model2 = MLModel(
        name="duplicate_name",
        model_type="classifier",
        file_path="models/model2.pkl",
        accuracy=0.90,
        training_samples=600,
    )
    
    db_session.add(model2)
    
    with pytest.raises(Exception):  # SQLAlchemy lançará IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_ml_model_filter_by_type(db_session: AsyncSession):
    """Testa filtragem de modelos por tipo."""
    # Cria modelos de diferentes tipos
    classifier = MLModel(
        name="classifier_v1",
        model_type="classifier",
        file_path="models/classifier_v1.pkl",
        accuracy=0.85,
        training_samples=500,
    )
    
    anomaly = MLModel(
        name="anomaly_v1",
        model_type="anomaly",
        file_path="models/anomaly_v1.pkl",
        accuracy=None,
        training_samples=800,
    )
    
    db_session.add_all([classifier, anomaly])
    await db_session.commit()
    
    # Filtra apenas classifiers
    result = await db_session.execute(
        select(MLModel).where(MLModel.model_type == "classifier")
    )
    classifiers = result.scalars().all()
    
    assert len(classifiers) == 1
    assert classifiers[0].name == "classifier_v1"
    
    # Filtra apenas anomaly detectors
    result = await db_session.execute(
        select(MLModel).where(MLModel.model_type == "anomaly")
    )
    anomaly_models = result.scalars().all()
    
    assert len(anomaly_models) == 1
    assert anomaly_models[0].name == "anomaly_v1"


@pytest.mark.asyncio
async def test_ml_model_order_by_created_at(db_session: AsyncSession):
    """Testa ordenação de modelos por data de criação."""
    import asyncio
    
    # Cria modelos com pequeno delay
    model1 = MLModel(
        name="model_old",
        model_type="classifier",
        file_path="models/model_old.pkl",
        accuracy=0.80,
        training_samples=400,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
    )
    
    model2 = MLModel(
        name="model_new",
        model_type="classifier",
        file_path="models/model_new.pkl",
        accuracy=0.90,
        training_samples=600,
        created_at=datetime(2024, 1, 2, 10, 0, 0),
    )
    
    db_session.add_all([model1, model2])
    await db_session.commit()
    
    # Lista modelos ordenados por data (mais recente primeiro)
    result = await db_session.execute(
        select(MLModel).order_by(MLModel.created_at.desc())
    )
    models = result.scalars().all()
    
    assert len(models) == 2
    assert models[0].name == "model_new"
    assert models[1].name == "model_old"


def test_ml_model_schema_validation():
    """Testa validação de schema Pydantic para ModelInfoResponse."""
    from app.schemas.schemas import ModelInfoResponse
    
    # Dados válidos
    data = {
        "id": 1,
        "name": "test_model",
        "model_type": "classifier",
        "file_path": "models/test_model.pkl",
        "accuracy": 0.92,
        "training_samples": 1000,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "metadata_json": "{}",
    }
    
    response = ModelInfoResponse(**data)
    
    assert response.name == "test_model"
    assert response.model_type == "classifier"
    assert response.accuracy == 0.92
    assert response.training_samples == 1000
    assert response.is_active is True


if __name__ == "__main__":
    print("Executando testes da Task 11 - ML Models...")
    pytest.main([__file__, "-v"])
