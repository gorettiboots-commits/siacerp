# -*- mode: python ; coding: utf-8 -*-
"""Especificación PyInstaller para SIAC ERP (empresa onedir).

Uso:
    pyinstaller siacerp.spec --noconfirm

Genera dist/SIACERP/SIACERP.exe con la app en _internal/.
Los datos del usuario (config.ini y goretti_erp.db) viven en %APPDATA%\SIAC
(ver directorio_datos() en src/database/db_manager.py), no en la carpeta
del .exe. Los archivos de la raíz empaquetados son plantillas/solo-lectura:
config.example.ini, video.mp4 y default.jpg.
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.example.ini', '.'),
        ('video.mp4', '.'),
        ('default.jpg', '.'),
        ('src/utils/styles.qss', 'src/utils'),
        ('src/database/schema.sql', 'src/database'),
        ('src/views/assets', 'src/views/assets'),
    ],
    hiddenimports=[
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SIACERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='src/views/assets/siac_icono.ico',
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='SIACERP',
)
