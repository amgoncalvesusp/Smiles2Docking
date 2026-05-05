# Changelog

## 1.1.1 - 2026-05-05

- Added `.pdbqt` export support in the workflow, CLI, and desktop interface.
- Kept `.pdbqt` generation on the existing Open Babel subprocess path, without introducing a new project dependency.
- Renamed the product consistently to `SMILES2Docking`.
- Added Nailton Monteiro do Nascimento Júnior to project authorship metadata and documentation.
- Updated Windows and Linux packaging metadata to use the `SMILES2Docking` product name.
- Documented the 1.1.1 macOS release decision: do not bundle MOPAC; if MOPAC is already installed, the app can use a manually configured executable path or the system `PATH`.
