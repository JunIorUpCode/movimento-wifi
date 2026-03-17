#!/usr/bin/env python3
"""
Script de validação do WiFiSense Local
Verifica se todos os componentes estão funcionando corretamente
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")

def check_python_version():
    """Verifica versão do Python"""
    print_info("Verificando versão do Python...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (requer 3.10+)")
        return False

def check_node_version():
    """Verifica versão do Node.js"""
    print_info("Verificando versão do Node.js...")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        major = int(version.split('.')[0].replace('v', ''))
        if major >= 18:
            print_success(f"Node.js {version}")
            return True
        else:
            print_error(f"Node.js {version} (requer 18+)")
            return False
    except FileNotFoundError:
        print_error("Node.js não encontrado")
        return False

def check_backend_structure():
    """Verifica estrutura de pastas do backend"""
    print_info("Verificando estrutura do backend...")
    required_dirs = [
        'backend/app',
        'backend/app/api',
        'backend/app/capture',
        'backend/app/processing',
        'backend/app/detection',
        'backend/app/services',
        'backend/app/models',
        'backend/app/schemas',
        'backend/app/db',
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"  {dir_path}")
        else:
            print_error(f"  {dir_path} (não encontrado)")
            all_ok = False
    
    return all_ok

def check_frontend_structure():
    """Verifica estrutura de pastas do frontend"""
    print_info("Verificando estrutura do frontend...")
    required_dirs = [
        'frontend/src',
        'frontend/src/components',
        'frontend/src/pages',
        'frontend/src/hooks',
        'frontend/src/services',
        'frontend/src/store',
        'frontend/src/types',
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"  {dir_path}")
        else:
            print_error(f"  {dir_path} (não encontrado)")
            all_ok = False
    
    return all_ok

def check_backend_files():
    """Verifica arquivos principais do backend"""
    print_info("Verificando arquivos do backend...")
    required_files = [
        'backend/app/main.py',
        'backend/app/api/routes.py',
        'backend/app/api/websocket.py',
        'backend/app/capture/mock_provider.py',
        'backend/app/processing/signal_processor.py',
        'backend/app/detection/heuristic_detector.py',
        'backend/app/services/monitor_service.py',
        'backend/requirements.txt',
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"  {file_path}")
        else:
            print_error(f"  {file_path} (não encontrado)")
            all_ok = False
    
    return all_ok

def check_frontend_files():
    """Verifica arquivos principais do frontend"""
    print_info("Verificando arquivos do frontend...")
    required_files = [
        'frontend/src/App.tsx',
        'frontend/src/main.tsx',
        'frontend/src/index.css',
        'frontend/src/pages/Dashboard.tsx',
        'frontend/src/pages/History.tsx',
        'frontend/src/pages/Settings.tsx',
        'frontend/src/hooks/useWebSocket.ts',
        'frontend/src/store/useStore.ts',
        'frontend/package.json',
        'frontend/vite.config.ts',
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"  {file_path}")
        else:
            print_error(f"  {file_path} (não encontrado)")
            all_ok = False
    
    return all_ok

def check_backend_dependencies():
    """Verifica se dependências do backend estão instaladas"""
    print_info("Verificando dependências do backend...")
    
    if not Path('backend/venv').exists():
        print_warning("  Ambiente virtual não encontrado (backend/venv)")
        print_info("  Execute: cd backend && python -m venv venv")
        return False
    
    # Tenta importar módulos principais
    sys.path.insert(0, str(Path('backend').absolute()))
    
    modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
    all_ok = True
    
    for module in modules:
        try:
            __import__(module)
            print_success(f"  {module}")
        except ImportError:
            print_error(f"  {module} (não instalado)")
            all_ok = False
    
    if not all_ok:
        print_info("  Execute: cd backend && pip install -r requirements.txt")
    
    return all_ok

def check_frontend_dependencies():
    """Verifica se dependências do frontend estão instaladas"""
    print_info("Verificando dependências do frontend...")
    
    if not Path('frontend/node_modules').exists():
        print_warning("  node_modules não encontrado")
        print_info("  Execute: cd frontend && npm install")
        return False
    
    print_success("  node_modules encontrado")
    return True

def test_backend_import():
    """Testa se o backend pode ser importado"""
    print_info("Testando importação do backend...")
    
    try:
        sys.path.insert(0, str(Path('backend').absolute()))
        from app.main import app
        print_success("  app.main importado com sucesso")
        
        from app.services.monitor_service import monitor_service
        print_success("  monitor_service importado com sucesso")
        
        from app.capture.mock_provider import MockSignalProvider
        print_success("  MockSignalProvider importado com sucesso")
        
        return True
    except Exception as e:
        print_error(f"  Erro ao importar: {e}")
        return False

def check_documentation():
    """Verifica se documentação existe"""
    print_info("Verificando documentação...")
    
    docs = ['README.md', 'GUIA_RAPIDO.md', 'ARQUITETURA.md', 'INTEGRACAO_HARDWARE.md']
    all_ok = True
    
    for doc in docs:
        if Path(doc).exists():
            print_success(f"  {doc}")
        else:
            print_warning(f"  {doc} (não encontrado)")
            all_ok = False
    
    return all_ok

def check_scripts():
    """Verifica se scripts de inicialização existem"""
    print_info("Verificando scripts de inicialização...")
    
    scripts = ['start_backend.bat', 'start_frontend.bat']
    all_ok = True
    
    for script in scripts:
        if Path(script).exists():
            print_success(f"  {script}")
        else:
            print_warning(f"  {script} (não encontrado)")
            all_ok = False
    
    return all_ok

def main():
    """Executa todas as verificações"""
    print_header("WiFiSense Local - Validação do Sistema")
    
    results = {}
    
    # Verificações de ambiente
    print_header("1. Verificando Ambiente")
    results['python'] = check_python_version()
    results['node'] = check_node_version()
    
    # Verificações de estrutura
    print_header("2. Verificando Estrutura de Pastas")
    results['backend_structure'] = check_backend_structure()
    results['frontend_structure'] = check_frontend_structure()
    
    # Verificações de arquivos
    print_header("3. Verificando Arquivos Principais")
    results['backend_files'] = check_backend_files()
    results['frontend_files'] = check_frontend_files()
    
    # Verificações de dependências
    print_header("4. Verificando Dependências")
    results['backend_deps'] = check_backend_dependencies()
    results['frontend_deps'] = check_frontend_dependencies()
    
    # Teste de importação
    print_header("5. Testando Importações")
    results['backend_import'] = test_backend_import()
    
    # Documentação e scripts
    print_header("6. Verificando Documentação e Scripts")
    results['documentation'] = check_documentation()
    results['scripts'] = check_scripts()
    
    # Resumo
    print_header("Resumo da Validação")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTestes passados: {passed}/{total}\n")
    
    if passed == total:
        print_success("✓ Todos os testes passaram!")
        print_info("\nPróximos passos:")
        print("  1. Execute: start_backend.bat")
        print("  2. Execute: start_frontend.bat")
        print("  3. Acesse: http://localhost:5173")
        return 0
    else:
        print_warning(f"⚠ {total - passed} teste(s) falharam")
        print_info("\nVerifique os erros acima e corrija antes de continuar.")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Validação interrompida pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Erro inesperado: {e}{Colors.END}")
        sys.exit(1)
