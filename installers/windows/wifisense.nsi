; WiFiSense Local — Script NSIS (Nullsoft Scriptable Install System)
; Cria instalador .exe com interface gráfica para Windows 10/11
; Compilar: makensis wifisense.nsi

;--------------------------------
; Configuração geral
!define PRODUCT_NAME      "WiFiSense Local"
!define PRODUCT_VERSION   "1.0.0"
!define PRODUCT_PUBLISHER "WiFiSense"
!define PRODUCT_URL       "https://wifisense.com"
!define PRODUCT_EXE       "wifisense-backend.exe"
!define INSTALL_DIR       "$PROGRAMFILES64\WiFiSense"
!define UNINSTALL_KEY     "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "WiFiSense-Setup-${PRODUCT_VERSION}.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

;--------------------------------
; Páginas do instalador
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "PortugueseBR"

;--------------------------------
; Seção principal
Section "WiFiSense Local" SecMain
  SectionIn RO  ; obrigatório

  SetOutPath "$INSTDIR"

  ; Copia os arquivos do build PyInstaller
  File /r "..\..\dist\wifisense\*.*"

  ; Cria arquivo .env padrão se não existir
  IfFileExists "$INSTDIR\.env" skip_env
  FileOpen $0 "$INSTDIR\.env" w
  FileWrite $0 "# WiFiSense Local — Configuração$\r$\n"
  FileWrite $0 "HOST=0.0.0.0$\r$\n"
  FileWrite $0 "PORT=8000$\r$\n"
  FileWrite $0 "DB_PATH=$INSTDIR\data\wifisense.db$\r$\n"
  FileWrite $0 "LOG_LEVEL=INFO$\r$\n"
  FileClose $0
  skip_env:

  ; Cria diretório de dados
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\models"

  ; Registra no Windows
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName"      "${PRODUCT_NAME}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion"   "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher"        "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "URLInfoAbout"     "${PRODUCT_URL}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation"  "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString"  "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify"       1
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair"       1

  ; Cria atalhos
  CreateDirectory "$SMPROGRAMS\WiFiSense"
  CreateShortcut "$SMPROGRAMS\WiFiSense\WiFiSense Local.lnk" \
    "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0
  CreateShortcut "$SMPROGRAMS\WiFiSense\Desinstalar WiFiSense.lnk" \
    "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\WiFiSense Local.lnk" \
    "$INSTDIR\${PRODUCT_EXE}"

  ; Instala serviço Windows (sc.exe)
  ExecWait 'sc create "WiFiSenseSvc" binPath= "$INSTDIR\${PRODUCT_EXE}" start= auto DisplayName= "WiFiSense Local Service"'
  ExecWait 'sc description "WiFiSenseSvc" "Detecção de movimento e presença via Wi-Fi"'
  ExecWait 'sc start "WiFiSenseSvc"'

  ; Desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

;--------------------------------
; Desinstalador
Section "Uninstall"
  ExecWait 'sc stop "WiFiSenseSvc"'
  ExecWait 'sc delete "WiFiSenseSvc"'

  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\WiFiSense"
  Delete "$DESKTOP\WiFiSense Local.lnk"

  DeleteRegKey HKLM "${UNINSTALL_KEY}"
SectionEnd
