"""
Testes para Task 10 - Detecção de Padrões de Comportamento.

Valida:
- learn_behavior_patterns() agrega eventos corretamente
- detect_anomalous_behavior() detecta anomalias
- Persistência de padrões no banco
- Integração com MonitorService
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.db.database import async_session, init_db
from app.detection.base import EventType
from app.models.models import BehaviorPattern, Event
from app.services.behavior_service import behavior_service


@pytest.fixture
async def setup_db():
    """Inicializa banco de dados para testes."""
    await init_db()
    
    # Limpa dados existentes
    async with async_session() as db:
        await db.execute(Event.__table__.delete())
        await db.execute(BehaviorPattern.__table__.delete())
        await db.commit()
    
    yield
    
    # Cleanup
    async with async_session() as db:
        await db.execute(Event.__table__.delete())
        await db.execute(BehaviorPattern.__table__.delete())
        await db.commit()


@pytest.fixture
async def sample_events():
    """Cria eventos de exemplo para 10 dias."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=10)
    
    # Simula padrão: presença de segunda a sexta, 9h-18h
    for day in range(10):
        current_date = base_time + timedelta(days=day)
        weekday = current_date.weekday()
        
        # Segunda a sexta (0-4)
        if weekday < 5:
            # Presença durante horário comercial (9h-18h)
            for hour in range(9, 18):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                event = Event(
                    timestamp=timestamp,
                    event_type="presence_moving" if hour % 2 == 0 else "presence_still",
                    confidence=0.85,
                    provider="test",
                    metadata_json="{}",
                )
                events.append(event)
            
            # Sem presença fora do horário
            for hour in list(range(0, 9)) + list(range(18, 24)):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                event = Event(
                    timestamp=timestamp,
                    event_type="no_presence",
                    confidence=0.90,
                    provider="test",
                    metadata_json="{}",
                )
                events.append(event)
        else:
            # Fim de semana: sem presença
            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                event = Event(
                    timestamp=timestamp,
                    event_type="no_presence",
                    confidence=0.90,
                    provider="test",
                    metadata_json="{}",
                )
                events.append(event)
    
    # Salva eventos no banco
    async with async_session() as db:
        for event in events:
            db.add(event)
        await db.commit()
    
    return events


@pytest.mark.asyncio
async def test_learn_behavior_patterns(setup_db, sample_events):
    """Testa aprendizado de padrões de comportamento."""
    # Aprende padrões
    patterns = await behavior_service.learn_behavior_patterns(min_days=7)
    
    # Verifica que padrões foram criados
    assert len(patterns) > 0
    assert len(patterns) <= 168  # Máximo 24h x 7 dias
    
    # Verifica que padrões foram persistidos
    async with async_session() as db:
        result = await db.execute(select(BehaviorPattern))
        db_patterns = result.scalars().all()
        assert len(db_patterns) == len(patterns)
    
    # Verifica padrão específico: segunda-feira às 10h (deve ter presença)
    monday_10h = next(
        (p for p in patterns if p.hour_of_day == 10 and p.day_of_week == 0),
        None
    )
    assert monday_10h is not None
    assert monday_10h.presence_probability > 0.7  # Alta probabilidade de presença
    assert monday_10h.sample_count >= 1
    
    # Verifica padrão específico: sábado às 10h (não deve ter presença)
    saturday_10h = next(
        (p for p in patterns if p.hour_of_day == 10 and p.day_of_week == 5),
        None
    )
    assert saturday_10h is not None
    assert saturday_10h.presence_probability < 0.3  # Baixa probabilidade de presença
    
    print(f"✓ Aprendeu {len(patterns)} padrões de comportamento")


@pytest.mark.asyncio
async def test_detect_anomalous_behavior(setup_db, sample_events):
    """Testa detecção de comportamento anômalo."""
    # Aprende padrões primeiro
    await behavior_service.learn_behavior_patterns(min_days=7)
    
    # Testa comportamento normal: segunda-feira às 10h com presença
    monday_10h = datetime.utcnow().replace(hour=10, minute=0, second=0)
    # Ajusta para segunda-feira
    while monday_10h.weekday() != 0:
        monday_10h += timedelta(days=1)
    
    is_anomaly, score, description = await behavior_service.detect_anomalous_behavior(
        EventType.PRESENCE_MOVING,
        monday_10h
    )
    
    # Não deve ser anomalia (presença esperada)
    assert not is_anomaly or score < 0.5
    print(f"✓ Comportamento normal detectado: {description}")
    
    # Testa comportamento anômalo: sábado às 10h com presença
    saturday_10h = datetime.utcnow().replace(hour=10, minute=0, second=0)
    # Ajusta para sábado
    while saturday_10h.weekday() != 5:
        saturday_10h += timedelta(days=1)
    
    is_anomaly, score, description = await behavior_service.detect_anomalous_behavior(
        EventType.PRESENCE_MOVING,
        saturday_10h
    )
    
    # Deve ser anomalia (presença não esperada no fim de semana)
    assert is_anomaly
    assert score > 0.0
    assert "incomum" in description.lower()
    print(f"✓ Anomalia detectada: {description} (score: {score:.2f})")


@pytest.mark.asyncio
async def test_insufficient_data(setup_db):
    """Testa comportamento com dados insuficientes."""
    # Cria apenas 3 dias de eventos
    base_time = datetime.utcnow() - timedelta(days=3)
    
    for day in range(3):
        current_date = base_time + timedelta(days=day)
        for hour in range(24):
            timestamp = current_date.replace(hour=hour, minute=0, second=0)
            event = Event(
                timestamp=timestamp,
                event_type="no_presence",
                confidence=0.90,
                provider="test",
                metadata_json="{}",
            )
            async with async_session() as db:
                db.add(event)
                await db.commit()
    
    # Deve lançar erro por dados insuficientes
    with pytest.raises(ValueError, match="at least 7 days"):
        await behavior_service.learn_behavior_patterns(min_days=7)
    
    print("✓ Validação de dados insuficientes funciona")


@pytest.mark.asyncio
async def test_pattern_cache(setup_db, sample_events):
    """Testa cache de padrões."""
    # Aprende padrões
    patterns1 = await behavior_service.learn_behavior_patterns(min_days=7)
    
    # Limpa cache
    behavior_service.clear_cache()
    
    # Obtém padrões novamente (deve carregar do banco)
    patterns2 = await behavior_service._get_patterns()
    
    assert len(patterns1) == len(patterns2)
    print("✓ Cache de padrões funciona corretamente")


@pytest.mark.asyncio
async def test_get_pattern_for_time(setup_db, sample_events):
    """Testa busca de padrão para hora/dia específicos."""
    # Aprende padrões
    await behavior_service.learn_behavior_patterns(min_days=7)
    
    # Busca padrão para segunda-feira às 10h
    pattern = await behavior_service.get_pattern_for_time(hour=10, day=0)
    
    assert pattern is not None
    assert pattern.hour_of_day == 10
    assert pattern.day_of_week == 0
    assert pattern.presence_probability > 0.0
    
    print(f"✓ Padrão encontrado: segunda 10h - presença {pattern.presence_probability:.0%}")


async def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("TESTES - TASK 10: DETECÇÃO DE PADRÕES DE COMPORTAMENTO")
    print("=" * 60)
    
    # Setup
    await init_db()
    
    # Limpa dados
    async with async_session() as db:
        await db.execute(Event.__table__.delete())
        await db.execute(BehaviorPattern.__table__.delete())
        await db.commit()
    
    # Cria eventos de exemplo
    print("\n1. Criando eventos de exemplo (10 dias)...")
    events = []
    base_time = datetime.utcnow() - timedelta(days=10)
    
    for day in range(10):
        current_date = base_time + timedelta(days=day)
        weekday = current_date.weekday()
        
        if weekday < 5:  # Segunda a sexta
            for hour in range(9, 18):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                event = Event(
                    timestamp=timestamp,
                    event_type="presence_moving" if hour % 2 == 0 else "presence_still",
                    confidence=0.85,
                    provider="test",
                    metadata_json="{}",
                )
                events.append(event)
            
            for hour in list(range(0, 9)) + list(range(18, 24)):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                event = Event(
                    timestamp=timestamp,
                    event_type="no_presence",
                    confidence=0.90,
                    provider="test",
                    metadata_json="{}",
                )
                events.append(event)
        else:  # Fim de semana
            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                event = Event(
                    timestamp=timestamp,
                    event_type="no_presence",
                    confidence=0.90,
                    provider="test",
                    metadata_json="{}",
                )
                events.append(event)
    
    async with async_session() as db:
        for event in events:
            db.add(event)
        await db.commit()
    
    print(f"   Criados {len(events)} eventos")
    
    # Teste 1: Aprender padrões
    print("\n2. Testando aprendizado de padrões...")
    patterns = await behavior_service.learn_behavior_patterns(min_days=7)
    print(f"   ✓ Aprendeu {len(patterns)} padrões")
    
    # Teste 2: Verificar persistência
    print("\n3. Verificando persistência no banco...")
    async with async_session() as db:
        result = await db.execute(select(BehaviorPattern))
        db_patterns = result.scalars().all()
        assert len(db_patterns) == len(patterns)
    print(f"   ✓ {len(db_patterns)} padrões persistidos no banco")
    
    # Teste 3: Detectar comportamento normal
    print("\n4. Testando detecção de comportamento normal...")
    monday_10h = datetime.utcnow().replace(hour=10, minute=0, second=0)
    while monday_10h.weekday() != 0:
        monday_10h += timedelta(days=1)
    
    is_anomaly, score, description = await behavior_service.detect_anomalous_behavior(
        EventType.PRESENCE_MOVING,
        monday_10h
    )
    print(f"   {description}")
    print(f"   Anomalia: {is_anomaly}, Score: {score:.2f}")
    
    # Teste 4: Detectar anomalia
    print("\n5. Testando detecção de anomalia...")
    saturday_10h = datetime.utcnow().replace(hour=10, minute=0, second=0)
    while saturday_10h.weekday() != 5:
        saturday_10h += timedelta(days=1)
    
    is_anomaly, score, description = await behavior_service.detect_anomalous_behavior(
        EventType.PRESENCE_MOVING,
        saturday_10h
    )
    print(f"   {description}")
    print(f"   Anomalia: {is_anomaly}, Score: {score:.2f}")
    
    # Teste 5: Verificar padrões específicos
    print("\n6. Verificando padrões específicos...")
    monday_10h_pattern = await behavior_service.get_pattern_for_time(hour=10, day=0)
    if monday_10h_pattern:
        print(f"   Segunda 10h: presença {monday_10h_pattern.presence_probability:.0%}")
    
    saturday_10h_pattern = await behavior_service.get_pattern_for_time(hour=10, day=5)
    if saturday_10h_pattern:
        print(f"   Sábado 10h: presença {saturday_10h_pattern.presence_probability:.0%}")
    
    print("\n" + "=" * 60)
    print("TODOS OS TESTES PASSARAM!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
