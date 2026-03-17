@echo off
echo ========================================
echo WiFiSense Local - Iniciando Backend
echo ========================================
echo.

cd backend

echo [1/3] Verificando ambiente virtual...
if not exist "venv\" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo [2/3] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo [3/3] Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo Backend rodando em http://localhost:8000
echo Pressione Ctrl+C para parar
echo ========================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
