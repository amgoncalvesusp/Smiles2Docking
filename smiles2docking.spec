# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

import PySide6
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


project_root = Path.cwd()
pyside_root = Path(PySide6.__file__).resolve().parent

rdkit_hiddenimports = sorted(
    set(
        collect_submodules("rdkit")
        + [
            "rdkit",
            "rdkit.rdBase",
            "rdkit.DataStructs",
            "rdkit.Geometry",
            "rdkit.Chem",
            "rdkit.Chem.AllChem",
            "rdkit.Chem.Draw",
            "rdkit.Chem.EnumerateStereoisomers",
            "rdkit.Chem.rdDepictor",
            "rdkit.Chem.rdDistGeom",
            "rdkit.Chem.rdForceFieldHelpers",
            "rdkit.Chem.rdchem",
            "rdkit.Chem.rdmolfiles",
            "rdkit.Chem.rdmolops",
        ]
    )
)

hiddenimports = sorted(
    set(
        rdkit_hiddenimports
        + [
            "openpyxl",
            "openpyxl.cell",
            "openpyxl.reader.excel",
            "openpyxl.styles",
            "xlrd",
            "pandas",
            "yaml",
            "PIL",
            "matplotlib",
        ]
    )
)

datas = collect_data_files("rdkit") + [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "config"), "config"),
    (str(project_root / "docs"), "docs"),
    (str(project_root / "data" / "raw"), "data/raw"),
    (str(project_root / "vendor" / "mopac"), "vendor/mopac"),
    (str(project_root / "vendor" / "openbabel"), "openbabel"),
    (str(project_root / "README.md"), "."),
    (str(project_root / "AUTHORS.md"), "."),
    (str(project_root / "CITATION.cff"), "."),
    (str(project_root / "LICENSE"), "."),
    (str(project_root / "packaging" / "qt.conf"), "."),
    (str(pyside_root / "plugins" / "platforms"), "platforms"),
]

binaries = collect_dynamic_libs("rdkit")

excludes = [
    "tests",
    "docs",
    "examples",
    ".git",
    "__pycache__",
    "*.pyc",
    "IPython",
    "jupyter",
    "PyQt5",
    "PyQt6",
    "tkinter",
]

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyinstaller_qt_runtime.py")],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="smiles2docking",
    icon=str(project_root / "assets" / "caffeine_icon.ico"),
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
    name="smiles2docking",
)
