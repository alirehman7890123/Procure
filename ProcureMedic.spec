# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


PROJECT_ROOT = Path(SPECPATH).resolve().parent
PACKAGE_PARENT = str(PROJECT_ROOT.parent)

datas = [('res', 'res'), ('styles', 'styles'), ('manufacturers.csv', '.'), ('master_products.csv', '.'), ('licensing/public_key.json', 'licensing'), ('purchase/med-template.ods', 'purchase')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
hiddenimports += collect_submodules('medic')


a = Analysis(
    ['starting.py'],
    pathex=[PACKAGE_PARENT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='ProcureMedic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
