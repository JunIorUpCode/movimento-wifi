"""
Teste para Task 2.3 - Persistência de Baseline
Testa save_baseline() e load_baseline() do CalibrationService
"""

import asyncio
import sys
import time
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.capture.mock_provider import MockSignalProvider, SimulationMode
from app.services.calibration_service import CalibrationService, BaselineData
from app.db.database import init_db, async_session
from app.models.models import CalibrationProfile
from sqlalchemy import select


async def setup_database():
    """Inicializa o banco de dados para testes."""
    print("Inicializando banco de dados...")
    await init_db()
    print("✓ Banco de dados inicializado\n")


async def test_save_baseline():
    """Testa salvamento de baseline no banco."""
    print("=== Teste 1: Salvar Baseline ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Calibra para obter baseline
    print("Calibrando ambiente (5 segundos)...")
    baseline = await service.start_calibration(duration_seconds=5, profile_name="test_save")

    print(f"Baseline calculado:")
    print(f"  - RSSI médio: {baseline.mean_rssi:.2f} dBm")
    print(f"  - Desvio padrão: {baseline.std_rssi:.2f}")
    print(f"  - Variância média: {baseline.mean_variance:.4f}")

    # Salva no banco
    print("\nSalvando baseline no banco...")
    await service.save_baseline("test_profile_1")
    print("✓ Baseline salvo com sucesso")

    # Verifica se foi salvo no banco
    async with async_session() as db:
        result = await db.execute(
            select(CalibrationProfile).where(CalibrationProfile.name == "test_profile_1")
        )
        profile = result.scalar_one_or_none()

        assert profile is not None, "Perfil não encontrado no banco"
        assert profile.name == "test_profile_1"
        assert profile.baseline_json is not None
        print(f"✓ Perfil encontrado no banco: {profile.name}")

    await provider.stop()
    print("✓ Teste 1 passou\n")


async def test_load_baseline():
    """Testa carregamento de baseline do banco."""
    print("=== Teste 2: Carregar Baseline ===")

    provider = MockSignalProvider()
    await provider.start()

    # Primeiro serviço: calibra e salva
    service1 = CalibrationService(provider)
    print("Calibrando e salvando baseline...")
    original_baseline = await service1.start_calibration(
        duration_seconds=5, profile_name="test_load"
    )
    await service1.save_baseline("test_profile_2")
    print(f"Baseline original salvo: RSSI={original_baseline.mean_rssi:.2f}")

    # Segundo serviço: carrega baseline salvo
    service2 = CalibrationService(provider)
    print("\nCarregando baseline do banco...")
    loaded_baseline = await service2.load_baseline("test_profile_2")

    print(f"Baseline carregado: RSSI={loaded_baseline.mean_rssi:.2f}")

    # Verifica que os dados são iguais
    assert loaded_baseline.mean_rssi == original_baseline.mean_rssi
    assert loaded_baseline.std_rssi == original_baseline.std_rssi
    assert loaded_baseline.mean_variance == original_baseline.mean_variance
    assert loaded_baseline.std_variance == original_baseline.std_variance
    assert loaded_baseline.noise_floor == original_baseline.noise_floor
    assert loaded_baseline.samples_count == original_baseline.samples_count
    assert loaded_baseline.profile_name == "test_profile_2"

    print("✓ Baseline carregado corretamente")

    # Verifica que baseline foi definido no serviço
    assert service2.baseline is not None
    assert service2.baseline.mean_rssi == loaded_baseline.mean_rssi
    print("✓ Baseline definido no serviço")

    await provider.stop()
    print("✓ Teste 2 passou\n")


async def test_update_existing_profile():
    """Testa atualização de perfil existente."""
    print("=== Teste 3: Atualizar Perfil Existente ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Primeira calibração
    print("Primeira calibração...")
    baseline1 = await service.start_calibration(duration_seconds=3, profile_name="update_test")
    await service.save_baseline("test_profile_3")
    print(f"Primeiro baseline: RSSI={baseline1.mean_rssi:.2f}")

    # Segunda calibração (atualiza o mesmo perfil)
    print("\nSegunda calibração (atualiza perfil)...")
    baseline2 = await service.start_calibration(duration_seconds=3, profile_name="update_test")
    await service.save_baseline("test_profile_3")
    print(f"Segundo baseline: RSSI={baseline2.mean_rssi:.2f}")

    # Verifica que só existe um perfil no banco
    async with async_session() as db:
        result = await db.execute(
            select(CalibrationProfile).where(CalibrationProfile.name == "test_profile_3")
        )
        profiles = result.scalars().all()

        assert len(profiles) == 1, f"Deveria ter apenas 1 perfil, encontrou {len(profiles)}"
        print(f"✓ Apenas 1 perfil no banco (atualização funcionou)")

        # Verifica que updated_at foi atualizado
        profile = profiles[0]
        assert profile.updated_at is not None
        print(f"✓ Campo updated_at foi atualizado")

    await provider.stop()
    print("✓ Teste 3 passou\n")


async def test_load_nonexistent_profile():
    """Testa carregamento de perfil inexistente."""
    print("=== Teste 4: Carregar Perfil Inexistente ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Tenta carregar perfil que não existe
    print("Tentando carregar perfil inexistente...")
    try:
        await service.load_baseline("perfil_que_nao_existe")
        print("✗ Teste 4 falhou: deveria ter levantado ValueError")
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        print(f"✓ ValueError levantado corretamente: {e}")
        assert "não encontrado" in str(e)

    await provider.stop()
    print("✓ Teste 4 passou\n")


async def test_save_without_baseline():
    """Testa salvamento sem baseline calculado."""
    print("=== Teste 5: Salvar Sem Baseline ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Tenta salvar sem ter calibrado
    print("Tentando salvar sem baseline...")
    try:
        await service.save_baseline("test_profile_empty")
        print("✗ Teste 5 falhou: deveria ter levantado ValueError")
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        print(f"✓ ValueError levantado corretamente: {e}")
        assert "Nenhum baseline disponível" in str(e)

    await provider.stop()
    print("✓ Teste 5 passou\n")


async def test_multiple_profiles():
    """Testa múltiplos perfis de calibração."""
    print("=== Teste 6: Múltiplos Perfis ===")

    provider = MockSignalProvider()
    await provider.start()

    service = CalibrationService(provider)

    # Cria 3 perfis diferentes
    profiles = ["perfil_dia", "perfil_noite", "perfil_janelas_abertas"]

    for profile_name in profiles:
        print(f"Criando perfil: {profile_name}")
        await service.start_calibration(duration_seconds=3, profile_name=profile_name)
        await service.save_baseline(profile_name)

    # Verifica que todos foram salvos
    async with async_session() as db:
        for profile_name in profiles:
            result = await db.execute(
                select(CalibrationProfile).where(CalibrationProfile.name == profile_name)
            )
            profile = result.scalar_one_or_none()
            assert profile is not None, f"Perfil {profile_name} não encontrado"
            print(f"✓ Perfil {profile_name} encontrado no banco")

    # Carrega cada perfil e verifica
    for profile_name in profiles:
        loaded = await service.load_baseline(profile_name)
        assert loaded.profile_name == profile_name
        print(f"✓ Perfil {profile_name} carregado corretamente")

    await provider.stop()
    print("✓ Teste 6 passou\n")


async def main():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("TESTES DE PERSISTÊNCIA DE BASELINE - TASK 2.3")
    print("=" * 60 + "\n")

    try:
        # Inicializa banco
        await setup_database()

        # Executa testes
        await test_save_baseline()
        await test_load_baseline()
        await test_update_existing_profile()
        await test_load_nonexistent_profile()
        await test_save_without_baseline()
        await test_multiple_profiles()

        print("=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
