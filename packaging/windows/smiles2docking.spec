# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

import PySide6
from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
)

project_root = Path.cwd()
env_prefix = Path(sys.prefix)
pyside_root = Path(PySide6.__file__).resolve().parent


def _resolve_qt_platforms_dir():
    candidates = [
        pyside_root / "plugins" / "platforms",
        env_prefix / "Library" / "lib" / "qt6" / "plugins" / "platforms",
        env_prefix / "Library" / "lib" / "qt5" / "plugins" / "platforms",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Qt 'platforms' plugin directory not found. Checked: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


qt_platforms_dir = _resolve_qt_platforms_dir()

rdkit_datas = collect_data_files("rdkit")
rdkit_binaries = collect_dynamic_libs("rdkit")
rdkit_hiddenimports = [
    "rdkit",
    "rdkit.rdBase",
    "rdkit.DataStructs",
    "rdkit.Chem",
    "rdkit.Chem.AllChem",
    "rdkit.Chem.rdchem",
    "rdkit.Chem.rdmolfiles",
    "rdkit.Chem.rdmolops",
    "rdkit.Chem.rdDistGeom",
    "rdkit.Chem.rdForceFieldHelpers",
]
pyside_datas = []
pyside_binaries = []
pyside_hiddenimports = []

# v0.3.0: Dimorphite-DL protonation backend.
# collect_all pulls the smarts/ data dir (site_substructures.smarts), which is a
# namespace package (no __init__.py); a bare collect_data_files would leave
# importlib.resources.files("dimorphite_dl.smarts") unresolvable in the frozen app.
dimorphite_datas, dimorphite_binaries, dimorphite_hiddenimports = collect_all("dimorphite_dl")
dimorphite_hiddenimports = sorted(set(dimorphite_hiddenimports + ["dimorphite_dl", "loguru"]))

# v1.3.0: MolGpKa default protonation backend (torch + torch-geometric only;
# the compiled torch-scatter/sparse stack is not required).
torch_datas, torch_binaries, torch_hiddenimports = collect_all("torch")
pyg_datas, pyg_binaries, pyg_hiddenimports = collect_all("torch_geometric")
molgpka_root = project_root / "src" / "protonation" / "molgpka"
molgpka_datas = [
    (str(molgpka_root / "models"), "src/protonation/molgpka/models"),
    (str(molgpka_root / "smarts_pattern.tsv"), "src/protonation/molgpka"),
    (str(molgpka_root / "LICENSE.md"), "src/protonation/molgpka"),
]
molgpka_hiddenimports = [
    "torch",
    "torch_geometric",
    "src.protonation.molgpka_adapter",
    "src.protonation.molgpka",
    "src.protonation.molgpka.net",
    "src.protonation.molgpka.gcn_conv",
    "src.protonation.molgpka.descriptor",
    "src.protonation.molgpka.ionization_group",
    "src.protonation.molgpka.predict_pka",
    "src.tautomer.factory",
    "src.tautomer.rdkit_adapter",
    "src.tautomer.sphysnet_adapter",
]

# v0.3.0: Meeko PDBQT writer
meeko_datas = collect_data_files("meeko")
meeko_hiddenimports = [
    "meeko",
]

# v1.2: Meeko transitive deps (structure I/O + geometry)
scipy_binaries = collect_dynamic_libs("scipy")
gemmi_binaries = collect_dynamic_libs("gemmi")
meeko_dep_hiddenimports = [
    "scipy",
    "gemmi",
]

# v0.3.0: joblib parallel
joblib_hiddenimports = [
    "joblib",
    "joblib.parallel",
    "joblib._multiprocessing_helpers",
    "joblib.externals.loky",
    "joblib.externals.loky.process_executor",
    "joblib.externals.cloudpickle",
]

openbabel_bin = env_prefix / "Library" / "bin"
openbabel_share = env_prefix / "share" / "openbabel"
openbabel_library_share = env_prefix / "Library" / "share" / "openbabel"

project_datas = [
    (str(project_root / "config"), "config"),
    (str(project_root / "docs"), "docs"),
    (str(project_root / "data" / "raw"), "data/raw"),
    (str(project_root / "vendor" / "mopac"), "vendor/mopac"),
    (str(project_root / "README.md"), "."),
    (str(project_root / "AUTHORS.md"), "."),
    (str(project_root / "CITATION.cff"), "."),
    (str(project_root / "LICENSE"), "."),
    (str(project_root / "packaging" / "qt.conf"), "."),
    (str(qt_platforms_dir), "platforms"),
]

openbabel_datas = []
openbabel_binaries = []

if openbabel_share.exists():
    openbabel_datas.append((str(openbabel_share), "openbabel/data"))
if openbabel_library_share.exists():
    openbabel_datas.append((str(openbabel_library_share), "openbabel/gui-data"))

for file_name in ("obabel.exe", "openbabel-3.dll"):
    candidate = openbabel_bin / file_name
    if candidate.exists():
        openbabel_binaries.append((str(candidate), "openbabel"))

for candidate in sorted(openbabel_bin.glob("*.obf")):
    openbabel_binaries.append((str(candidate), "openbabel"))

hiddenimports = sorted(
    set(
        rdkit_hiddenimports
        + pyside_hiddenimports
        + dimorphite_hiddenimports
        + meeko_hiddenimports
        + meeko_dep_hiddenimports
        + joblib_hiddenimports
        + torch_hiddenimports
        + pyg_hiddenimports
        + molgpka_hiddenimports
    )
)

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=rdkit_binaries + pyside_binaries + openbabel_binaries + scipy_binaries + gemmi_binaries + dimorphite_binaries + torch_binaries + pyg_binaries,
    datas=rdkit_datas + pyside_datas + project_datas + openbabel_datas + dimorphite_datas + meeko_datas + torch_datas + pyg_datas + molgpka_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyinstaller_qt_runtime.py")],
    excludes=[
        "matplotlib",
        "pytest",
        "tkinter",
        "sqlalchemy",
        "IPython",
        "jupyter",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SMILES2DockingDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    contents_directory=".",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SMILES2DockingDesktop",
)
