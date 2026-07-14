# SMILES2Docking v1.3.0

## English

This release overhauls protonation and adds an optional tautomer step, in
response to peer review.

### Protonation

- **New default backend: MolGpKa.** A graph neural network predicts per-atom
  pKa; an iterative titration protocol then re-predicts on the charged
  intermediate at each step to return the physically dominant protonation
  microstate at the target pH. This correctly returns the mono-cation for
  piperazine at pH 7.4, where independent per-site rules over-protonate.
- **Dimorphite-DL is now an enumeration backend.** Instead of silently
  returning one arbitrary state it returns every plausible protonation state
  (one exported structure per state). The legacy single-pick behaviour remains
  available as `dimorphite_pick`.
- Backends selectable in the GUI and `config/settings.yaml`
  (`molgpka | dimorphite | dimorphite_pick | openbabel | none`).

### Tautomers (optional, off by default)

- Optional dominant-tautomer selection before protonation: RDKit enumerates
  tautomers; the `rdkit` backend picks the canonical tautomer, and the
  `sphysnet` backend ranks with sPhysNet-Taut. sPhysNet-Taut is an optional
  extra and is **not** bundled (it needs the compiled torch-scatter/sparse
  stack and ships no explicit licence).

### Packaging notes

- MolGpKa ships bundled in all desktop packages (CPU PyTorch +
  torch-geometric; the compiled torch-scatter/sparse extensions are not
  required). Installers are correspondingly larger.
- Windows portable ZIP and installer include MOPAC 23.2.4; Linux/macOS do not
  bundle MOPAC. MOPAC refinement stays disabled by default.

---

# SMILES2Docking v1.2.1

## English

This release refreshes the desktop packages for Windows, Linux, and macOS.

### Packaging notes

- Windows portable ZIP and Windows installer include MOPAC 23.2.4.
- The Windows installer also places MOPAC in the standard path:
  `C:\Program Files\MOPAC\bin`.
- Linux and macOS packages do not bundle MOPAC. Install MOPAC separately on
  those systems if you want to enable semi-empirical refinement.
- MOPAC refinement is disabled by default in the application. Users can enable
  it manually when needed.

### Included artifacts

- Windows portable ZIP
- Windows installer
- Linux AppImage
- Linux tar.gz portable bundle
- macOS ZIP

### Fixes retained in this release

- Windows Qt/PySide6 packaging is pinned to the tested PySide6 runtime.
- Frozen builds include the required Qt runtime configuration.
- AppImage/frozen output paths use writable user directories.
- Dimorphite-DL data files are bundled for frozen builds.
- Meeko-based PDBQT export is included.

## Portugues

Este release atualiza os pacotes desktop para Windows, Linux e macOS.

### Notas de empacotamento

- O ZIP portatil do Windows e o instalador do Windows incluem MOPAC 23.2.4.
- O instalador do Windows tambem coloca o MOPAC no caminho padrao:
  `C:\Program Files\MOPAC\bin`.
- Os pacotes Linux e macOS nao incluem MOPAC. Instale o MOPAC separadamente
  nesses sistemas se quiser ativar o refinamento semiempirico.
- O refinamento com MOPAC fica desativado por padrao no aplicativo. O usuario
  pode ativa-lo manualmente quando desejar.

### Artefatos incluidos

- ZIP portatil para Windows
- Instalador para Windows
- AppImage para Linux
- Pacote portatil tar.gz para Linux
- ZIP para macOS

### Correcoes mantidas neste release

- O empacotamento Qt/PySide6 do Windows esta fixado no runtime PySide6 testado.
- Builds congelados incluem a configuracao necessaria do runtime Qt.
- Caminhos de saida em AppImage/builds congelados usam diretorios gravaveis do usuario.
- Os arquivos de dados do Dimorphite-DL sao incluidos nos builds congelados.
- A exportacao PDBQT baseada em Meeko esta incluida.
