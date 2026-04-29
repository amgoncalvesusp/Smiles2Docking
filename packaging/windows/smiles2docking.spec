# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
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

openbabel_bin = env_prefix / "Library" / "bin"
openbabel_share = env_prefix / "share" / "openbabel"
openbabel_library_share = env_prefix / "Library" / "share" / "openbabel"

project_datas = [
    (str(project_root / "assets"), "assets"),
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

mopac_binaries = []
mopac_datas = []
bundle_mopac = os.environ.get("SMILES2DOCKINGFULL_BUNDLE_MOPAC", "").strip().lower() in {"1", "true", "yes", "on"}
if bundle_mopac:
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    mopac_roots = [env_prefix, program_files / "MOPAC"]
    for root in mopac_roots:
        for binary_dir in (root / "Library" / "bin", root / "bin"):
            if not (binary_dir / "mopac.exe").exists():
                continue
            for file_name in ("mopac.exe", "mopac.dll", "libiomp5md.dll"):
                binary_candidate = binary_dir / file_name
                if binary_candidate.exists():
                    mopac_binaries.append((str(binary_candidate), "mopac"))
            break
        if mopac_binaries:
            for doc_candidate in (root / "LICENSE", root / "CITATION.cff"):
                if doc_candidate.exists():
                    mopac_datas.append((str(doc_candidate), "docs/mopac"))
            break

hiddenimports = sorted(set(rdkit_hiddenimports))

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=rdkit_binaries + openbabel_binaries + mopac_binaries,
    datas=rdkit_datas + project_datas + openbabel_datas + mopac_datas,
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
    name="SMILES2DockingFULL",
    icon=str(project_root / "assets" / "caffeine_icon.ico"),
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
    name="SMILES2DockingFULL",
)
