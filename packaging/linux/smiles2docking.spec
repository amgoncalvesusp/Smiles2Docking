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

openbabel_bin = env_prefix / "bin"
openbabel_lib = env_prefix / "lib"
openbabel_share = env_prefix / "share" / "openbabel"

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
openbabel_data_candidates = [openbabel_share]
if openbabel_share.exists():
    openbabel_data_candidates.extend(sorted(path for path in openbabel_share.iterdir() if path.is_dir()))

for candidate in openbabel_data_candidates:
    if (candidate / "phmodel.txt").exists():
        openbabel_datas.append((str(candidate), "openbabel/data"))
        break

for candidate in openbabel_data_candidates:
    if (candidate / "splash.png").exists():
        openbabel_datas.append((str(candidate), "openbabel/gui-data"))
        break

linux_binary = openbabel_bin / "obabel"
if linux_binary.exists():
    openbabel_binaries.append((str(linux_binary), "openbabel/bin"))

for candidate in sorted(openbabel_lib.glob("libopenbabel*.so*")):
    openbabel_binaries.append((str(candidate), "openbabel/lib"))

plugin_roots = [openbabel_lib / "openbabel"]
plugin_roots.extend(sorted(path for path in (openbabel_lib / "openbabel").glob("*") if path.is_dir()))
for root in plugin_roots:
    for candidate in sorted(root.glob("*.so*")):
        openbabel_binaries.append((str(candidate), "openbabel/plugins"))

mopac_binaries = []
bundle_mopac = os.environ.get("SMILES2DOCKINGFULL_BUNDLE_MOPAC", "").strip().lower() in {"1", "true", "yes", "on"}
if bundle_mopac:
    for binary_dir in (env_prefix / "bin", Path("/usr/bin")):
        candidate = binary_dir / "mopac"
        if candidate.exists():
            mopac_binaries.append((str(candidate), "mopac/bin"))
            break

hiddenimports = sorted(set(rdkit_hiddenimports))

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=rdkit_binaries + openbabel_binaries + mopac_binaries,
    datas=rdkit_datas + project_datas + openbabel_datas,
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
