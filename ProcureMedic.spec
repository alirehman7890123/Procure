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
excluded_hiddenimport_prefixes = (
    "medic.tests",
    "medic.purchase.test_",
    "medic.sales.test_",
    "medic.utilities.test_",
)
excluded_hiddenimport_suffixes = (
    ".conftest",
)
excluded_data_path_parts = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "tests",
}
runtime_excludes = [
    "pytest",
    "_pytest",
    "pluggy",
    "py",
    "pygments",
    "iniconfig",
    "tomli",
    "cx_Freeze",
    "setuptools",
    "wheel",
    "pip",
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
]


def _extend_package_collection(package_name):
    hiddenimports.extend(collect_submodules(package_name))
    datas.extend(collect_data_files(package_name))


def _should_include_hiddenimport(module_name):
    normalized_name = str(module_name or "").strip()
    if not normalized_name:
        return False
    if normalized_name.endswith(excluded_hiddenimport_suffixes):
        return False
    if normalized_name.startswith(excluded_hiddenimport_prefixes):
        return False
    return True


def _should_include_data_file(data_entry):
    if not isinstance(data_entry, tuple) or len(data_entry) < 2:
        return False

    source_path = Path(str(data_entry[0]))
    try:
        relative_path = source_path.relative_to(project_dir)
    except ValueError:
        relative_path = source_path

    if any(part in excluded_data_path_parts for part in relative_path.parts):
        return False
    if source_path.name.startswith("test_") and source_path.suffix == ".py":
        return False
    if source_path.name == "conftest.py":
        return False
    return True


# Canonical package surface.
_extend_package_collection("medic")

# De-duplicate while preserving order for stable builds, and skip tests and
# packaging-only helpers that should never ship in production bundles.
hiddenimports = [
    module_name
    for module_name in dict.fromkeys(hiddenimports)
    if _should_include_hiddenimport(module_name)
]
datas = [
    data_entry
    for data_entry in dict.fromkeys(datas)
    if _should_include_data_file(data_entry)
]

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
datas = [
    data_entry
    for data_entry in dict.fromkeys(datas)
    if _should_include_data_file(data_entry)
]


a = Analysis(
    ["starting.py"],
    pathex=[str(project_dir), str(package_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=runtime_excludes,
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
    exclude_binaries=False,
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
