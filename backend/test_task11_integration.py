"""
Teste de integração para Task 11 - Endpoints REST de ML Models.

Testa os endpoints:
- GET /api/ml/models
- POST /api/ml/models/{name}/activate

Requisitos: 8.1, 8.2
"""

import json
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.database import async_session
from app.main import app
from app.models.models import MLModel


@pytest.mark.asyncio
async def test_list_ml_models_endpoint():
    """Testa endpoint GET /api/ml/models."""
    # Cria alguns modelos no banco
    async with async_session() as db:
        models = [
            MLModel(
                name="test_classifier_v1",
                model_type="classifier",
                file_path="models/test_classifier_v1.pkl",
                accuracy=0.85,
                training_samples=500,
            ),
            MLModel(
                name="test_classifier_v2",
                model_type="classifier",
                file_path="models/test_classifier_v2.pkl",
                accuracy=0.92,
                training_samples=1000,
                is_active=True,
            ),
        ]
        
        for model in models:
            db.add(model)
        
        await db.commit()
    
    # Testa endpoint
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/ml/models")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 2
    assert any(m["name"] == "test_classifier_v1" for m in data)
    assert any(m["name"] == "test_classifier_v2" for m in data)
    
    # Verifica que modelo ativo está marcado
    active_model = next(m for m in data if m["name"] == "test_classifier_v2")
    assert active_model["is_active"] is True


@pytest.mark.asyncio
async def test_activate_ml_model_endpoint():
    """Testa endpoint POST /api/ml/models/{name}/activate."""
    # Cria modelos no banco
    async with async_session() as db:
        model1 = MLModel(
            name="test_model_inactive",
            model_type="classifier",
            file_path="models/test_model_inactive.pkl",
            accuracy=0.80,
            training_samples=400,
            is_active=False,
        )
        
        model2 = MLModel(
            name="test_model_to_activate",
            model_type="classifier",
            file_path="models/test_model_to_activate.pkl",
            accuracy=0.90,
            training_samples=600,
            is_active=False,
        )
        
        db.add_all([model1, model2])
        await db.commit()
    
    # Ativa o segundo modelo
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/ml/models/test_model_to_activate/activate")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "activated"
    assert data["model"]["name"] == "test_model_to_activate"
    assert data["model"]["is_active"] is True
    
    # Verifica no banco que apenas o modelo ativado está ativo
    async with async_session() as db:
        result = await db.execute(
            select(MLModel).where(MLModel.model_type == "classifier")
        )
        models = result.scalars().all()
        
        active_models = [m for m in models if m.is_active]
        assert len(active_models) == 1
        assert active_models[0].name == "test_model_to_activate"


@pytest.mark.asyncio
async def test_activate_nonexistent_model():
    """Testa ativação de modelo que não existe."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/ml/models/nonexistent_model/activate")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


if __name__ == "__main__":
    print("Executando testes de integração da Task 11...")
    pytest.main([__file__, "-v"])
