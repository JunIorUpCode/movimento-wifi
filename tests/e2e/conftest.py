# conftest.py — Configuração dos testes E2E
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: testes end-to-end (requer serviços rodando)")


def pytest_collection_modifyitems(config, items):
    """Marca todos os testes deste diretório como e2e."""
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
