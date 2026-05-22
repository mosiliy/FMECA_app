# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller fmeca_app.spec
# Результат: dist/FMECA_Analysis/FMECA_Analysis.exe

import sys
from pathlib import Path

block_cipher = None
project_dir = Path(SPECPATH)

datas = [
    (str(project_dir / 'fonts'), 'fonts'),
]

# Скрытые импорты для matplotlib / pandas / reportlab / openpyxl
hiddenimports = [
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
    'pandas',
    'openpyxl',
    'openpyxl.cell._writer',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.lib.utils',
    'seaborn',
    'networkx',
    'PIL',
    'PIL._imagingtk',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
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
    name='FMECA_Analysis',
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
    name='FMECA_Analysis',
)
