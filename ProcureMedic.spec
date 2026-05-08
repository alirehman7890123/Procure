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
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

hiddenimports = ["medic"]
datas = []


def _extend_package_collection(package_name):
    hiddenimports.extend(collect_submodules(package_name))
    datas.extend(collect_data_files(package_name))


# Canonical package surface.
_extend_package_collection("medic")

# De-duplicate while preserving order for stable builds.
hiddenimports = list(dict.fromkeys(hiddenimports))
datas = list(dict.fromkeys(datas))

# Non-package runtime assets that live at the repo root must be added
# explicitly; these used to come from the old CLI `--add-data` workflow.
extra_datas = [
    (str(project_dir / "licensing" / "public_key.json"), "licensing"),
    (str(project_dir / "manufacturers.csv"), "."),
    (str(project_dir / "master_products.csv"), "."),
    (str(project_dir / "purchase" / "med-template.ods"), "purchase"),
]

for pattern in ("*.css",):
    for path in (project_dir / "styles").glob(pattern):
        extra_datas.append((str(path), "styles"))

for path in (project_dir / "res").rglob("*"):
    if path.is_file():
        extra_datas.append((str(path), str(Path("res") / path.relative_to(project_dir / "res").parent)))

datas.extend(extra_datas)
datas = list(dict.fromkeys(datas))


a = Analysis(
    ["starting.py"],
    pathex=[str(workspace_root), str(project_dir)],
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
