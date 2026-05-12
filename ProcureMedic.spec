import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_dir = Path(SPECPATH).resolve()
package_dir = project_dir / "medic"

# Make the project root importable before PyInstaller's collection helpers
# run so the sibling `medic` package resolves consistently in CI and local
# packaging runs.
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

# Runtime assets now live inside the `medic` package directory and must be
# added explicitly because they are not Python packages.
extra_datas = [
    (str(package_dir / "licensing" / "public_key.json"), "licensing"),
    (str(package_dir / "manufacturers.csv"), "."),
    (str(package_dir / "master_products.csv"), "."),
    (str(package_dir / "purchase" / "med-template.ods"), "purchase"),
]

for pattern in ("*.css",):
    for path in (package_dir / "styles").glob(pattern):
        extra_datas.append((str(path), "styles"))

for path in (package_dir / "res").rglob("*"):
    if path.is_file():
        extra_datas.append((str(path), str(Path("res") / path.relative_to(package_dir / "res").parent)))

datas.extend(extra_datas)
datas = list(dict.fromkeys(datas))


a = Analysis(
    ["starting.py"],
    pathex=[str(project_dir), str(package_dir)],
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
