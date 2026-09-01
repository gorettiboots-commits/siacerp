# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para SIAC ERP."""

import os
from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None

# ── Archivos de datos (se copian al lado del .exe) ──────────────
datas = [
    (str(ROOT / 'src' / 'database' / 'schema.sql'), 'src/database'),
    (str(ROOT / 'src' / 'utils' / 'styles.qss'), 'src/utils'),
    (str(ROOT / 'src' / 'views' / 'assets'), 'src/views/assets'),
    (str(ROOT / 'icon.png'), '.'),
    (str(ROOT / 'config.example.ini'), '.'),
    (str(ROOT / 'scripts' / 'pre_configurar.py'), 'scripts'),
]

# ── Imports ocultos ─────────────────────────────────────────────
hiddenimports = [
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'bcrypt',
    'openpyxl',
    'reportlab',
    'PIL',
    'psycopg2',
]

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SIAC_ERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'src' / 'views' / 'assets' / 'siac_icono.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SIAC_ERP',
)
