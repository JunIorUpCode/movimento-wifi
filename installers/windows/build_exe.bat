@echo off
REM WiFiSense Local — Build do instalador Windows (.exe)
REM Requisitos: Python 3.11+, PyInstaller, NSIS (makensis no PATH)

setlocal
cd /d "%~dp0..\.."

echo [1/4] Instalando dependencias de build...
python -m pip install pyinstaller --quiet

echo [2/4] Gerando executavel com PyInstaller...
pyinstaller installers\windows\wifisense.spec --distpath dist --workpath build\pyinstaller --noconfirm
if errorlevel 1 (
    echo ERRO: PyInstaller falhou.
    exit /b 1
)

echo [3/4] Compilando instalador NSIS...
where makensis >nul 2>&1
if errorlevel 1 (
    echo AVISO: makensis nao encontrado. Baixe NSIS em https://nsis.sourceforge.io
    echo        O executavel esta em: dist\wifisense\
    goto :done
)
makensis installers\windows\wifisense.nsi
if errorlevel 1 (
    echo ERRO: NSIS falhou.
    exit /b 1
)

echo [4/4] Pronto!
echo Instalador gerado: WiFiSense-Setup-1.0.0.exe

:done
endlocal
