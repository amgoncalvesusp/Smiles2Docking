# -*- mode: python ; coding: utf-8 -*-
# macOS build spec. Mirrors packaging/linux/smiles2docking.spec but collects
# Open Babel as .dylib/.so from the (conda) environment prefix and wraps the
# COLLECT tree in a .app bundle. Open Babel and RDKit are expected to come from
# conda-forge; MOPAC/PM7 is not bundled (same as the Linux build).
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all

project_root = Path.cwd()
env_prefix = Path(sys.prefix)

rdkit_datas, rdkit_binaries, rdkit_hiddenimports = collect_all("rdkit")
matplotlib_datas, matplotlib_binaries, matplotlib_hiddenimports = collect_all("matplotlib")
dimorphite_datas, dimorphite_binaries, dimorphite_hiddenimports = collect_all("dimorphite_dl")
meeko_datas, meeko_binaries, meeko_hiddenimports = collect_all("meeko")
scipy_datas, scipy_binaries, scipy_hiddenimports = collect_all("scipy")
gemmi_datas, gemmi_binaries, gemmi_hiddenimports = collect_all("gemmi")
pyside_datas = []
pyside_binaries = []
pyside_hiddenimports = []

openbabel_bin = env_prefix / "bin"
openbabel_lib = env_prefix / "lib"
openbabel_share = env_prefix / "share" / "openbabel"

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

mac_binary = openbabel_bin / "obabel"
if mac_binary.exists():
    openbabel_binaries.append((str(mac_binary), "openbabel/bin"))

for pattern in ("libopenbabel*.dylib", "libopenbabel*.so*"):
    for candidate in sorted(openbabel_lib.glob(pattern)):
        openbabel_binaries.append((str(candidate), "openbabel/lib"))

plugin_roots = [openbabel_lib / "openbabel"]
plugin_roots.extend(sorted(path for path in (openbabel_lib / "openbabel").glob("*") if path.is_dir()))

for root in plugin_roots:
    for pattern in ("*.dylib", "*.so*"):
        for candidate in sorted(root.glob(pattern)):
            openbabel_binaries.append((str(candidate), "openbabel/plugins"))

hiddenimports = sorted(
    set(
        rdkit_hiddenimports
        + matplotlib_hiddenimports
        + pyside_hiddenimports
        + dimorphite_hiddenimports
        + meeko_hiddenimports
        + scipy_hiddenimports
        + gemmi_hiddenimports
        + ["matplotlib.backends.backend_pdf"]
    )
)

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=rdkit_binaries + matplotlib_binaries + pyside_binaries + openbabel_binaries
    + dimorphite_binaries + meeko_binaries + scipy_binaries + gemmi_binaries,
    datas=rdkit_datas + matplotlib_datas + pyside_datas + project_datas + openbabel_datas
    + dimorphite_datas + meeko_datas + scipy_datas + gemmi_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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

app = BUNDLE(
    coll,
    name="SMILES2Docking.app",
    icon=None,
    bundle_identifier="org.usp.smiles2docking",
)
