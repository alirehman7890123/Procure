import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_dir = Path(SPECPATH).resolve()
workspace_root = project_dir.parent

# Make the parent of the `medic` package importable before PyInstaller's
# collection helpers run; otherwise collect_submodules("medic") can resolve
# to an empty set in CI when the checkout root is the package directory.
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

hiddenimports = collect_submodules("medic")
datas = collect_data_files("medic")


a = Analysis(
    ["starting.py"],
    pathex=[str(workspace_root)],
    binaries=[],
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
    [],
    exclude_binaries=True,
    name="ProcureMedic",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ProcureMedic",
)
