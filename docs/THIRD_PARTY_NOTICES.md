# Third-Party Notices

This project bundles or depends on the components below. License names and source references should be rechecked at release time if dependency versions change.

## Runtime Dependencies

### RDKit

- Purpose: cheminformatics core, 2D/3D structure handling and export preparation
- License: BSD-3-Clause
- References:
  - [RDKit official repository](https://github.com/rdkit/rdkit)
  - [RDKit Book](https://mail.rdkit.org/docs/RDKit_Book.html)

### Open Babel

- Purpose: protonation state handling and MOL2 conversion
- License basis used for distribution assessment: GPL family, historically documented around GPL version 2
- References:
  - [Open Babel documentation](https://openbabel.org/api/2.0.2/)
  - [Open Babel project site](https://openbabel.org/)

### pandas

- Purpose: spreadsheet ingestion and tabular processing
- License: BSD-style according to project documentation
- Reference:
  - [pandas documentation](https://pandas.pydata.org/pandas-docs/version/1.3.1/index.html)

### openpyxl

- Purpose: Excel `.xlsx` reading
- License: MIT/Expat
- Reference:
  - [openpyxl documentation](https://openpyxl.readthedocs.io/en/2.6/)

### PyYAML

- Purpose: configuration loading
- License: MIT
- Reference:
  - [PyYAML official repository](https://github.com/yaml/pyyaml)

### MOPAC

- Purpose: PM7 semiempirical quantum refinement
- License: Apache-2.0 for current open-source releases; older open-source releases were distributed under LGPL terms
- References:
  - [OpenMOPAC GitHub repository](https://github.com/openmopac/mopac)
  - [OpenMOPAC manual](https://openmopac.net/Manual/index.html)

### PySide6

- Purpose: desktop graphical interface
- License model stated by the project: LGPLv3/GPLv3/commercial
- Reference:
  - [Qt for Python](https://doc.qt.io/qtforpython-6.5/)

## Build and Development Dependencies

### PyInstaller

- Purpose: Windows and Linux executable bundling
- License: GPL 2.0 with a special exception for generated bundles; certain files under Apache 2.0
- References:
  - [PyInstaller Manual](https://pyinstaller.org/en/stable/)
  - [PyInstaller License](https://pyinstaller.org/en/stable/license.html)

### pytest

- Purpose: automated tests
- License: MIT
- Reference:
  - [pytest license](https://docs.pytest.org/en/7.1.x/license.html)

## Distribution Note

This repository is prepared for open distribution. If dependency versions are updated, review the authoritative license pages above before publishing a new binary release.
