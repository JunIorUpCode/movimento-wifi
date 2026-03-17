# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — WiFiSense Local Backend (Windows)
# Uso: pyinstaller wifisense.spec

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent.parent  # raiz do projeto
BACKEND = ROOT / "backend"

a = Analysis(
    [str(BACKEND / "app" / "main.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=[
        (str(BACKEND / "models"), "models"),
        (str(BACKEND / "docs"), "docs"),
        (str(ROOT / "shared"), "shared"),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "cryptography",
        "sklearn",
        "numpy",
        "scipy",
        "sqlalchemy",
        "aiosqlite",
        "pydantic",
        "fastapi",
        "starlette",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "tests", "_pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="wifisense-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="wifisense",
)
