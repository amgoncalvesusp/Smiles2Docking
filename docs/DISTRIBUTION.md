# Distribution Guide

## Scope

`SMILES2Docking` is intended for open distribution as a packaged desktop application and as source code.

## Project Identity

- Name: SMILES2Docking
- Authors: Adriano Marques Goncalves; Daniel Grajales Ruiz; Nailton Monteiro do Nascimento Júnior
- Affiliations: Universidade de Araraquara - UNIARA; IQ/UNESP
- Contact: amgoncalves@uniara.edu.br
- Project license: GPL-2.0-or-later

## Distribution Model

The recommended Windows distribution is a `PyInstaller` one-folder build generated from `packaging/windows/smiles2docking.spec`.

The recommended Linux distribution is a portable `PyInstaller` build staged as an `AppDir` and archived as `tar.gz`, generated from `packaging/linux/smiles2docking.spec`.

The generated application bundles:

- the Python runtime
- the PySide6 desktop interface
- the RDKit runtime
- the Open Babel executable and data files
- the local project code
- optionally the MOPAC runtime, only when explicitly requested during the build

This means end users do not need to install Python separately.

## Open-Source Distribution Requirements

When distributing a binary build, also distribute or publish alongside it:

1. The corresponding source code of this project.
2. The project license file.
3. The third-party notices file.
4. Any copyright and attribution notices required by bundled dependencies.

## MOPAC Note

SMILES2Docking integrates PM7 refinement through MOPAC. To keep the package as light as possible, the default build does not bundle the MOPAC runtime. The software first checks a user-configured executable path, then a bundled copy if present, then the system `PATH`, and finally the default local installation directory.

If bundling is desired for a specific release, set `SMILES2DOCKING_BUNDLE_MOPAC=1` before running the build.

## Multiplatform MOPAC Bundle Status for 1.1.1

Verified on 2026-05-04:

- Official MOPAC repository: https://github.com/openmopac/mopac
- Official download page: https://openmopac.net/download/
- Official installation notes: https://openmopac.net/download/installer/
- Latest official release observed: MOPAC 23.2.4, listed on GitHub and the MOPAC download page.
- License: Apache-2.0 for the current open-source MOPAC distribution.
- Linux x86_64: official self-contained archive exists at `https://github.com/openmopac/mopac/releases/download/v23.2.4/mopac-23.2.4-linux.tar.gz`.
- macOS Intel x86_64: official self-contained archive exists at `https://github.com/openmopac/mopac/releases/download/v23.2.4/mopac-23.2.4-mac.zip`.
- macOS Apple Silicon: no native bundled MOPAC runtime will be included in the 1.1.1 release. The official installation notes state that the macOS version is presently built for x86 processors and should run on Apple Silicon through Rosetta; no official native Apple Silicon self-contained archive was identified.

Release decision for 1.1.1:

- Windows: the existing release flow may still bundle MOPAC when explicitly requested.
- Linux: keep the current optional MOPAC bundling behavior.
- macOS: do not bundle MOPAC in the release package.
- macOS user note: if MOPAC is already installed on the target machine, the application can still use it either from the configured executable path in the interface/settings or from the system `PATH`.

## Build Procedure

1. Activate the `smiles2docking` environment.
2. Ensure `mopac.exe` is installed locally, or set `SMILES2DOCKING_BUNDLE_MOPAC=1` if you intentionally want to bundle it.
3. Run `packaging/windows/build_executable.bat`.
4. Distribute the generated `SMILES2Docking/` folder together with:
   - `LICENSE`
   - `AUTHORS.md`
   - `CITATION.cff`
   - `docs/THIRD_PARTY_NOTICES.md`

For Linux:

1. Activate the `smiles2docking` environment on a Linux `x86_64` machine.
2. Ensure `mopac` is available in the environment, or set `SMILES2DOCKING_BUNDLE_MOPAC=1` if you intentionally want to bundle it.
3. Run `packaging/linux/build_portable.sh`.
4. Distribute the generated portable archive, plus the source archive generated in the same release directory.

## Recommended Release Contents

- executable folder or portable archive
- project source archive
- third-party notices
- license file
- citation file
