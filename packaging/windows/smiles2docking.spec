# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

project_root = Path.cwd()
env_prefix = Path(sys.prefix)

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

# v0.3.0: Dimorphite-DL protonation backend
dimorphite_datas = collect_data_files("dimorphite_dl")
dimorphite_hiddenimports = [
    "dimorphite_dl",
    "loguru",
]

# v0.3.0: Meeko PDBQT writer
meeko_datas = collect_data_files("meeko")
meeko_hiddenimports = [
    "meeko",
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
    (str(project_root / "README.md"), "."),
    (str(project_root / "AUTHORS.md"), "."),
    (str(project_root / "CITATION.cff"), "."),
    (str(project_root / "LICENSE"), "."),
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
        + joblib_hiddenimports
    )
)

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=rdkit_binaries + pyside_binaries + openbabel_binaries,
    datas=rdkit_datas + pyside_datas + project_datas + openbabel_datas + dimorphite_datas + meeko_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SMILES2DockingDesktop",
)
