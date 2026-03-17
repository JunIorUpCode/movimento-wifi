@echo off
echo ========================================
echo WiFiSense Local - Iniciando Frontend
echo ========================================
echo.

cd frontend

echo [1/2] Verificando dependencias...
if not exist "node_modules\" (
    echo Instalando dependencias do npm...
    call npm install
) else (
    echo Dependencias ja instaladas.
)

echo [2/2] Iniciando servidor de desenvolvimento...
echo.
echo ========================================
echo Frontend rodando em http://localhost:5173
echo Pressione Ctrl+C para parar
echo ========================================
echo.

call npm run dev
