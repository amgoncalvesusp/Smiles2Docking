# Linux Distribution Guide

## Scope

This project includes Linux packaging assets for a portable desktop distribution of `SMILES2DockingFULL` based on `PyInstaller`.

The Linux packaging workflow produces:

- an `AppDir` tree ready for local execution
- a portable `.tar.gz` archive for open distribution
- an optional `.AppImage` when `appimagetool` is available on the Linux build host
- a matching source-code archive for GPL-compatible redistribution

## Packaging Files

Linux packaging resources live in:

- `packaging/linux/build_portable.sh`
- `packaging/linux/smiles2docking.spec`
- `packaging/linux/AppRun`
- `packaging/linux/run_smiles2docking.sh`
- `packaging/linux/SMILES2DockingDesktop.desktop`
- `packaging/linux/smiles2docking.svg`

## Build Host Requirements

Build on a Linux `x86_64` machine with:

- `conda` or `mamba`
- the environment from `environment/environment.yml`
- `tar`
- optionally `appimagetool` for `.AppImage`
- optionally `mopac` if PM7 runtime bundling is desired

## Recommended Build Steps

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

## Generated Artifacts

The Linux build script writes to `release/linux`:

- `SMILES2DockingFULL-x86_64.AppDir`
- `SMILES2DockingFULL-linux-x86_64.tar.gz`
- `SMILES2DockingFULL-source.tar.gz`
- optionally `SMILES2DockingFULL-x86_64.AppImage`

## End-User Installation

For the portable archive:

```bash
tar -xzf SMILES2DockingFULL-linux-x86_64.tar.gz
cd SMILES2DockingFULL-x86_64.AppDir
./AppRun
```

To install a launcher in the current user session:

```bash
mkdir -p ~/.local/share/applications
cp SMILES2DockingDesktop.desktop ~/.local/share/applications/
```

If desired, update the `Exec=` and `Icon=` entries to the final extraction path.

## Runtime Notes

- The launcher exports `PATH` for bundled MOPAC and Open Babel binaries.
- The launcher exports `LD_LIBRARY_PATH` for bundled Open Babel shared libraries.
- If MOPAC is not bundled, the application can still use a system-installed `mopac`.
- The Linux spec only bundles `mopac` when `SMILES2DOCKINGFULL_BUNDLE_MOPAC=1` is set during the build.

## Distribution Checklist

Distribute together:

1. The Linux portable archive or AppImage.
2. The source archive generated in the same release.
3. `LICENSE`.
4. `AUTHORS.md`.
5. `CITATION.cff`.
6. `docs/THIRD_PARTY_NOTICES.md`.
