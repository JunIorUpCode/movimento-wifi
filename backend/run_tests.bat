@echo off
REM run_tests.bat — Executa suite de testes da Fase 5 com pytest + cobertura
REM
REM Uso:
REM   run_tests.bat            Executa todos os testes
REM   run_tests.bat unit       Apenas testes unitários
REM   run_tests.bat integ      Apenas testes de integração
REM   run_tests.bat perf       Apenas testes de performance
REM   run_tests.bat props      Apenas testes de propriedade (Hypothesis)
REM   run_tests.bat fast       Testes rápidos (exclui performance e Hypothesis)
REM   run_tests.bat coverage   Gera relatório de cobertura HTML

setlocal

REM === Configuração ===
set PYTHON=venv\Scripts\python.exe
set PYTEST=venv\Scripts\pytest.exe
set COVERAGE_MIN=70
set TEST_DIR=tests

REM Verifica se o venv existe
if not exist "%PYTHON%" (
    echo [ERRO] Ambiente virtual nao encontrado em venv\
    echo Execute: python -m venv venv ^& venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

REM Instala dependências de teste se necessário
%PYTHON% -m pip show pytest >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias de teste...
    %PYTHON% -m pip install pytest pytest-asyncio pytest-cov hypothesis -q
)

REM === Seleção de testes ===
set TARGET=%1

if "%TARGET%"=="unit" (
    echo [TEST] Executando testes unitarios core...
    %PYTHON% -m pytest %TEST_DIR%\test_unit_core.py -v --tb=short
    goto :check_exit
)

if "%TARGET%"=="integ" (
    echo [TEST] Executando testes de integracao...
    %PYTHON% -m pytest %TEST_DIR%\test_integration.py -v --tb=short
    goto :check_exit
)

if "%TARGET%"=="perf" (
    echo [TEST] Executando testes de performance...
    %PYTHON% -m pytest %TEST_DIR%\test_performance.py -v --tb=short -s
    goto :check_exit
)

if "%TARGET%"=="props" (
    echo [TEST] Executando testes de propriedade (Hypothesis)...
    %PYTHON% -m pytest %TEST_DIR%\test_properties.py -v --tb=short
    goto :check_exit
)

if "%TARGET%"=="fast" (
    echo [TEST] Executando testes rapidos (sem performance e sem Hypothesis)...
    %PYTHON% -m pytest %TEST_DIR%\test_unit_core.py %TEST_DIR%\test_integration.py -v --tb=short
    goto :check_exit
)

if "%TARGET%"=="coverage" (
    echo [TEST] Executando todos os testes com relatorio de cobertura...
    %PYTHON% -m pytest %TEST_DIR%\ ^
        --cov=app ^
        --cov-report=html:htmlcov ^
        --cov-report=term-missing ^
        --cov-fail-under=%COVERAGE_MIN% ^
        -v --tb=short
    if not errorlevel 1 (
        echo.
        echo [OK] Relatorio HTML gerado em: htmlcov\index.html
        start htmlcov\index.html
    )
    goto :check_exit
)

REM === Padrão: todos os testes com cobertura básica ===
echo ============================================================
echo  WiFiSense — Suite de Testes Fase 5
echo ============================================================
echo.
echo [1/4] Testes unitarios core...
%PYTHON% -m pytest %TEST_DIR%\test_unit_core.py -v --tb=short -q
set UNIT_EXIT=%errorlevel%

echo.
echo [2/4] Testes de integracao...
%PYTHON% -m pytest %TEST_DIR%\test_integration.py -v --tb=short -q
set INTEG_EXIT=%errorlevel%

echo.
echo [3/4] Testes de performance...
%PYTHON% -m pytest %TEST_DIR%\test_performance.py -v --tb=short -q -s
set PERF_EXIT=%errorlevel%

echo.
echo [4/4] Testes de propriedade (Hypothesis)...
%PYTHON% -m pytest %TEST_DIR%\test_properties.py -v --tb=short -q
set PROPS_EXIT=%errorlevel%

echo.
echo ============================================================
echo  Cobertura total...
echo ============================================================
%PYTHON% -m pytest %TEST_DIR%\ ^
    --cov=app ^
    --cov-report=term-missing ^
    --cov-fail-under=%COVERAGE_MIN% ^
    -q --tb=no
set COV_EXIT=%errorlevel%

echo.
echo ============================================================
echo  Resultado Final
echo ============================================================
set FAIL=0
if not "%UNIT_EXIT%"=="0" ( echo [FALHOU] Testes unitarios & set FAIL=1 )
if not "%INTEG_EXIT%"=="0" ( echo [FALHOU] Testes de integracao & set FAIL=1 )
if not "%PERF_EXIT%"=="0" ( echo [FALHOU] Testes de performance & set FAIL=1 )
if not "%PROPS_EXIT%"=="0" ( echo [FALHOU] Testes de propriedade & set FAIL=1 )
if not "%COV_EXIT%"=="0" ( echo [FALHOU] Cobertura abaixo de %COVERAGE_MIN%%% & set FAIL=1 )

if "%FAIL%"=="0" (
    echo [OK] Todos os testes passaram e cobertura >= %COVERAGE_MIN%%%
    exit /b 0
) else (
    echo [ERRO] Alguns testes falharam. Veja o output acima.
    exit /b 1
)

:check_exit
if errorlevel 1 (
    echo.
    echo [ERRO] Testes falharam.
    exit /b 1
) else (
    echo.
    echo [OK] Testes passaram.
    exit /b 0
)
