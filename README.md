[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19900623.svg)](https://doi.org/10.5281/zenodo.19900623)
# SMILES2Docking

Desktop application and Python workflow for preparing ligands from `SMI`, `TXT`, `CSV`, `TSV`, `XLS`, and `XLSX` files, protonating at a configurable pH, generating 3D structures, refining geometry with `PM7` in `MOPAC`, and exporting in `MOL2`, `SDF`, or `PDBQT`.

Aplicativo desktop e workflow Python para preparar ligantes a partir de arquivos `SMI`, `TXT`, `CSV`, `TSV`, `XLS` e `XLSX`, protonar em pH configuravel, gerar estruturas 3D, refinar a geometria com `PM7` no `MOPAC` e exportar em `MOL2`, `SDF` ou `PDBQT`.

## English

### Authors

- Adriano Marques Goncalves
- Universidade de Araraquara - UNIARA
- amgoncalves@uniara.edu.br
- Daniel Andres Grajales Ruiz
- IQ/UNESP
- daniel.g.ruiz@unesp.br
- Nailton Monteiro do Nascimento Junior
- IQ/UNESP

### Main capabilities

1. Load input data from `SMI`, `TXT`, `CSV`, `TSV`, `XLS`, and `XLSX` files with ID and SMILES columns.
2. Remove salts, counterions, and disconnected fragments when the main fragment can be identified.
3. Protonate using Open Babel at a configurable pH.
4. Generate 3D structures with RDKit.
5. Optimize geometry using the `MMFF94 -> MMFF94s -> UFF` cascade.
6. Refine the final structure with `MOPAC PM7` using `MMOK`, `XYZ`, `CHARGE=n`, and optional `EPS=n.nn`.
7. Optionally preserve native `MOPAC` job files.
8. Export as separate `.mol2`, `.sdf`, or `.pdbqt` files, or as a single file in one of those formats.
9. Generate a JSON report with processing audit information.
10. Generate a final log in the selected output directory.
11. Run via CLI or desktop graphical interface.

### Windows download

Windows users do not need to manually install Python, MOPAC, Open Babel, or dependencies.

Releases page:

https://github.com/amgoncalvesusp/Smiles2Docking/releases

Current installer:

https://github.com/amgoncalvesusp/Smiles2Docking/releases/download/v1.1.1/SMILES2DOCKING_Setup_v1.1.1_win64.exe

After downloading, run `SMILES2DOCKING_Setup_v1.1.1_win64.exe` and launch SMILES2DOCKING from the Windows Start menu.

Requirements:

- Windows 10 64-bit or later
- no separate Python installation
- no separate MOPAC installation
- no separate Open Babel installation

### Protonation states

The application determines the protonation state using Open Babel at the user-selected pH through the `obabel -p <pH>` step.

Practical validation:

- `CC(=O)O` at `pH 12` was converted to `CC(=O)[O-]`
- `CN` at `pH 2` was converted to `C[NH3+]`

### PM7 refinement

When the PM7 step is enabled, the application:

- calculates the final net charge of the protonated molecule
- builds a `.mop` file with `PM7 MMOK XYZ CHARGE=n`
- adds `EPS=78.39` by default for water, with an option to disable implicit solvent
- runs MOPAC and uses the final optimized geometry for export
- can preserve MOPAC job files in `mopac_files/` inside the output directory

MOPAC binary lookup order:

1. path configured in `config/settings.yaml`
2. binary bundled with the application
3. `mopac` in the `PATH`
4. `C:\Program Files\MOPAC\bin\mopac.exe` on Windows

macOS release note:

- the macOS package does not bundle MOPAC
- if MOPAC is already installed on the target machine, the application can use it from a manually configured executable path or from the system `PATH`

### Graphical interface

Run:

```bash
python scripts/run_gui.py
```

The interface allows you to:

- select the input file
- choose the Excel sheet
- adjust the `access_code` and `smiles` columns
- define the protonation pH
- enable or disable `PM7` refinement
- enable or disable implicit solvent with `EPS`
- choose whether native `MOPAC` files should be preserved
- manually provide the path to the `MOPAC` executable, if needed
- choose between separate `MOL2`, `SDF`, or `PDBQT` files, or a single file in one of those formats
- edit the output base name; in separate export mode it works as an optional prefix
- run in the background, minimizing the window and avoiding completion/error pop-ups
- switch the interface between English and Portuguese using a visible selector in the main window
- choose the final output directory for structures, JSON report, and execution log

### Command line

Example with PM7 enabled:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --ph 7.4 --pm7 --pm7-solvent --pm7-eps 78.39
```

Gas-phase example:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --no-pm7-solvent
```

Example with PM7 disabled:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --no-pm7
```

Example preserving MOPAC files:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --preserve-mopac-files
```

### Project structure

```text
SMILES2Docking/
|- AUTHORS.md
|- CITATION.cff
|- LICENSE
|- README.md
|- docs/
|- environment/
|- packaging/
|- config/
|- data/
|- logs/
|- scripts/
|- src/
`- tests/
```

### Environment

Suggested setup:

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

Note: the Windows installer distributed through GitHub Releases already includes the runtime required for desktop use. The Python environment described here is only necessary for development, testing, or generating new builds.

### Windows executable build

With the `smiles2docking` environment activated, run:

```bash
packaging\windows\build_executable.bat
```

The build generates a folder in `%LOCALAPPDATA%\SMILES2DockingBuild\dist\SMILES2Docking\`.

### Linux package build

On a Linux `x86_64` host, with the `smiles2docking` environment activated:

```bash
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

The process generates:

- a portable `AppDir`
- a distributable `tar.gz`
- a `tar.gz` containing the source code
- optionally an `.AppImage`, if `appimagetool` is installed

Full details are available in `docs/LINUX_DISTRIBUTION.md`.

### Open distribution and notices

Distribution and third-party documents are available in `docs/DISTRIBUTION.md` and `docs/THIRD_PARTY_NOTICES.md`.

### Project license

This repository is configured for open distribution under `GPL-2.0-or-later`, to maintain compatibility with the use of Open Babel in the distributed application. See `LICENSE`.

### GitHub publication

The project is published on GitHub with:

- source code for the workflow and desktop interface
- build scripts for Windows and Linux
- project license
- citation file
- identified authorship
- distribution documentation and third-party notices
- optional integration with MOPAC for PM7 refinement
- Windows installer distributed as a release asset

Windows releases:

https://github.com/amgoncalvesusp/Smiles2Docking/releases

## Portugues

### Autoria

- Adriano Marques Goncalves
- Universidade de Araraquara - UNIARA
- amgoncalves@uniara.edu.br
- Daniel Andres Grajales Ruiz
- IQ/UNESP
- daniel.g.ruiz@unesp.br
- Nailton Monteiro do Nascimento Junior
- IQ/UNESP

### Principais capacidades

1. Carregar entradas em `SMI`, `TXT`, `CSV`, `TSV`, `XLS` e `XLSX` com ID e SMILES.
2. Remover sais, contraions e fragmentos desconectados quando o fragmento principal e identificavel.
3. Protonar com Open Babel em pH configuravel.
4. Gerar estruturas 3D com RDKit.
5. Otimizar geometria com a cascata `MMFF94 -> MMFF94s -> UFF`.
6. Refinar a estrutura final com `MOPAC PM7` usando `MMOK`, `XYZ`, `CHARGE=n` e `EPS=n.nn` opcional.
7. Preservar opcionalmente os arquivos nativos do job do `MOPAC`.
8. Exportar em arquivos `.mol2`, `.sdf` ou `.pdbqt` separados, ou em um arquivo unico desses formatos.
9. Gerar relatorio JSON com auditoria do processamento.
10. Gerar log final na mesma pasta de saida escolhida.
11. Executar por CLI ou por interface grafica desktop.

### Download para Windows

Usuarios de Windows nao precisam instalar Python, MOPAC, Open Babel ou dependencias manualmente.

Pagina de releases:

https://github.com/amgoncalvesusp/Smiles2Docking/releases

Instalador atual:

https://github.com/amgoncalvesusp/Smiles2Docking/releases/download/v1.1.1/SMILES2DOCKING_Setup_v1.1.1_win64.exe

Depois de baixar, execute `SMILES2DOCKING_Setup_v1.1.1_win64.exe` e abra o SMILES2DOCKING pelo menu Iniciar do Windows.

Requisitos:

- Windows 10 64-bit ou superior
- nenhuma instalacao separada de Python
- nenhuma instalacao separada de MOPAC
- nenhuma instalacao separada de Open Babel

### Estados de protonacao

O aplicativo determina o estado de protonacao usando o Open Babel no pH selecionado pelo usuario, por meio da etapa `obabel -p <pH>`.

Validacao pratica:

- `CC(=O)O` em `pH 12` foi convertido para `CC(=O)[O-]`
- `CN` em `pH 2` foi convertido para `C[NH3+]`

### Refinamento PM7

Quando a etapa PM7 esta ativada, o aplicativo:

- calcula a carga liquida final da molecula protonada
- monta um arquivo `.mop` com `PM7 MMOK XYZ CHARGE=n`
- adiciona `EPS=78.39` por padrao para agua, com opcao de desativar o solvente implicito
- executa o MOPAC e usa a geometria otimizada final para exportacao
- pode preservar os arquivos do job do MOPAC em `mopac_files/` dentro do diretorio de saida

Busca do binario MOPAC:

1. caminho configurado em `config/settings.yaml`
2. binario empacotado junto com a aplicacao
3. `mopac` no `PATH`
4. `C:\Program Files\MOPAC\bin\mopac.exe` no Windows

Observacao para release macOS:

- o pacote macOS nao inclui MOPAC
- se o usuario ja tiver MOPAC instalado no computador, o programa pode usa-lo pelo caminho configurado manualmente ou pelo `PATH`

### Interface grafica

Execute:

```bash
python scripts/run_gui.py
```

A interface permite:

- selecionar o arquivo de entrada
- escolher a aba Excel
- ajustar as colunas `access_code` e `smiles`
- definir o pH de protonacao
- ativar ou desativar o refinamento `PM7`
- ativar ou desativar o solvente implicito com `EPS`
- escolher se os arquivos nativos do `MOPAC` devem ser preservados
- informar manualmente o caminho do executavel do `MOPAC`, se necessario
- escolher entre arquivos `MOL2`, `SDF` ou `PDBQT` separados, ou um arquivo unico desses formatos
- editar o nome base de saida; em exportacao separada ele funciona como prefixo opcional
- rodar em segundo plano, minimizando a janela e evitando pop-ups de conclusao/erro
- alternar a interface entre ingles e portugues por um seletor visivel na janela principal
- escolher o diretorio final para estruturas, relatorio JSON e log de execucao

### Linha de comando

Exemplo com PM7 ativo:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --ph 7.4 --pm7 --pm7-solvent --pm7-eps 78.39
```

Exemplo em fase gasosa:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --no-pm7-solvent
```

Exemplo desativando PM7:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --no-pm7
```

Exemplo preservando os arquivos do MOPAC:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --preserve-mopac-files
```

### Estrutura do projeto

```text
SMILES2Docking/
|- AUTHORS.md
|- CITATION.cff
|- LICENSE
|- README.md
|- docs/
|- environment/
|- packaging/
|- config/
|- data/
|- logs/
|- scripts/
|- src/
`- tests/
```

### Ambiente

Criacao sugerida:

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

Observacao: o instalador Windows distribuido em GitHub Releases ja inclui o runtime necessario para uso desktop. O ambiente Python descrito aqui e necessario apenas para desenvolvimento, testes ou geracao de novos builds.

### Build do executavel Windows

Use o ambiente `smiles2docking` ativo e rode:

```bash
packaging\windows\build_executable.bat
```

O build gera uma pasta em `%LOCALAPPDATA%\SMILES2DockingBuild\dist\SMILES2Docking\`.

### Build do pacote Linux

Em um host Linux `x86_64`, com o ambiente `smiles2docking` ativo:

```bash
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

O processo gera:

- um `AppDir` portatil
- um `tar.gz` distribuivel
- um `tar.gz` com o codigo-fonte
- opcionalmente um `.AppImage`, se `appimagetool` estiver instalado

Detalhes completos em `docs/LINUX_DISTRIBUTION.md`.

### Distribuicao aberta e notices

Os documentos de distribuicao e de terceiros estao em `docs/DISTRIBUTION.md` e `docs/THIRD_PARTY_NOTICES.md`.

### Licenca do projeto

Este repositorio esta configurado para distribuicao aberta sob `GPL-2.0-or-later`, para manter compatibilidade com o uso do Open Babel na aplicacao distribuida. Veja `LICENSE`.

### Publicacao no GitHub

O projeto esta publicado no GitHub com:

- codigo-fonte do workflow e da interface desktop
- scripts de build para Windows e Linux
- licenca do projeto
- arquivo de citacao
- autoria identificada
- documentacao de distribuicao e notices de terceiros
- integracao opcional com MOPAC para refinamento PM7
- instalador Windows distribuido como asset de release

Releases do Windows:

https://github.com/amgoncalvesusp/Smiles2Docking/releases
