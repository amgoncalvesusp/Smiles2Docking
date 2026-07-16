# -*- mode: python ; coding: utf-8 -*-
import glob
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all

project_root = Path.cwd()
env_prefix = Path(sys.prefix)

# v1.3.x Linux fix: PyInstaller's dependency scan can bundle the host's older
# libcrypto/libssl for the conda-forge _ssl extension (built against a newer
# OpenSSL), producing a runtime "version `OPENSSL_3.3.0' not found" error that
# breaks any backend importing ssl (e.g. MolGpKa via torch). Bundle the conda
# env's own OpenSSL libraries at the bundle root so _ssl resolves the matching
# versions. OpenBabel is unaffected because it shells out to a binary.
openssl_binaries = []
for _pattern in ("libssl.so*", "libcrypto.so*"):
    for _lib in glob.glob(str(env_prefix / "lib" / _pattern)):
        openssl_binaries.append((_lib, "."))

rdkit_datas, rdkit_binaries, rdkit_hiddenimports = collect_all("rdkit")
matplotlib_datas, matplotlib_binaries, matplotlib_hiddenimports = collect_all("matplotlib")
# v1.2: protonation (dimorphite) + PDBQT export (meeko + transitive scipy/gemmi)
dimorphite_datas, dimorphite_binaries, dimorphite_hiddenimports = collect_all("dimorphite_dl")

# v1.3.0: MolGpKa default protonation backend (torch + torch-geometric only).
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
    # Bundle the Linux MOPAC binary + its libraries under vendor/mopac so the
    # runtime resolver finds vendor/mopac/bin/mopac (RUNPATH $ORIGIN/../lib picks
    # up the libmopac/libiomp5 in vendor/mopac/lib).
    (str(project_root / "vendor" / "mopac-linux" / "bin"), "vendor/mopac/bin"),
    (str(project_root / "vendor" / "mopac-linux" / "lib"), "vendor/mopac/lib"),
    (str(project_root / "vendor" / "mopac-linux" / "LICENSE"), "vendor/mopac"),
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

plugin_roots = [
    openbabel_lib / "openbabel",
]
plugin_roots.extend(sorted(path for path in (openbabel_lib / "openbabel").glob("*") if path.is_dir()))

for root in plugin_roots:
    for candidate in sorted(root.glob("*.so*")):
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
        + torch_hiddenimports
        + pyg_hiddenimports
        + molgpka_hiddenimports
        + ["matplotlib.backends.backend_pdf"]
    )
)

a = Analysis(
    [str(project_root / "scripts" / "run_gui.py")],
    pathex=[str(project_root)],
    binaries=rdkit_binaries + matplotlib_binaries + pyside_binaries + openbabel_binaries
    + dimorphite_binaries + meeko_binaries + scipy_binaries + gemmi_binaries
    + torch_binaries + pyg_binaries + openssl_binaries,
    datas=rdkit_datas + matplotlib_datas + pyside_datas + project_datas + openbabel_datas
    + dimorphite_datas + meeko_datas + scipy_datas + gemmi_datas
    + torch_datas + pyg_datas + molgpka_datas,
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
