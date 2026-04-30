[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19900623.svg)](https://doi.org/10.5281/zenodo.19900623)
# SMILES2DockingFULL

Desktop application and Python workflow for preparing ligands from `SMI`, `TXT`, `CSV`, `TSV`, `XLS`, and `XLSX` files, protonating at a configurable pH, generating 3D structures, refining geometry with `PM7` in `MOPAC`, and exporting in `MOL2` or `SDF` format.

## Authors

- Adriano Marques Gonçalves
- University of Araraquara - UNIARA
- amgoncalves@uniara.edu.br
- Daniel Andrés Grajales Ruiz
- IQ/UNESP
- daniel.g.ruiz@unesp.br

## Main Capabilities

1. Load input data from `SMI`, `TXT`, `CSV`, `TSV`, `XLS`, and `XLSX` files with ID and SMILES columns.
2. Remove salts, counterions, and disconnected fragments when the main fragment can be identified.
3. Protonate using Open Babel at a configurable pH.
4. Generate 3D structures with RDKit.
5. Optimize geometry using the `MMFF94 -> MMFF94s -> UFF` cascade.
6. Refine the final structure with `MOPAC PM7` using `MMOK`, `XYZ`, `CHARGE=n`, and optional `EPS=n.nn`.
7. Optionally preserve the native `MOPAC` job files.
8. Export as separate `.mol2` files, separate `.sdf` files, a single `.mol2`, or a single `.sdf`.
9. Generate a JSON report with processing audit information.
10. Generate a final log in the selected output folder.
11. Run via CLI or desktop graphical interface.

## Windows Download

Windows users do not need to manually install Python, MOPAC, Open Babel, or dependencies.

Download the installer from the releases page:

https://github.com/amgoncalvesusp/Smiles2Docking/releases

Current file:

https://github.com/amgoncalvesusp/Smiles2Docking/releases/download/v1.0/SMILES2DOCKING_Setup_v1.0_win64.exe

After downloading, run `SMILES2DOCKING_Setup_v1.0_win64.exe` and launch SMILES2DOCKING from the Windows Start menu.

Requirements:

- Windows 10 64-bit or later.
- No separate Python installation.
- No separate MOPAC installation.
- No separate Open Babel installation.

## Protonation States

The application determines the protonation state using Open Babel at the user-selected pH through the `obabel -p <pH>` step.

Practical validation of this implementation:

- `CC(=O)O` at `pH 12` was converted to `CC(=O)[O-]`
- `CN` at `pH 2` was converted to `C[NH3+]`

This confirms that the application is adjusting protonation states according to pH for simple acid/base cases.

## PM7 Refinement

When the PM7 step is enabled, the application:

- calculates the final net charge of the protonated molecule
- builds a `.mop` file with `PM7 MMOK XYZ CHARGE=n`
- adds `EPS=78.39` by default for water, with an option to disable implicit solvent
- runs MOPAC and uses the final optimized geometry for export
- can preserve the MOPAC job files in `mopac_files/` inside the output directory

MOPAC binary lookup order:

1. path configured in `config/settings.yaml`
2. binary bundled with the application
3. `mopac` in the `PATH`
4. `C:\Program Files\MOPAC\bin\mopac.exe` on Windows

## Graphical Interface

Run:

```bash
python scripts/run_gui.py
The interface allows you to:

select the input file
choose the Excel sheet
adjust the access_code and smiles columns
define the protonation pH
enable or disable PM7 refinement
enable or disable implicit solvent with EPS
choose whether native MOPAC files should be preserved
manually provide the path to the MOPAC executable, if needed
choose between separate MOL2 files, separate SDF files, a single MOL2, or a single SDF
edit the output base name; in separate export mode it works as an optional prefix
run in the background, minimizing the window and avoiding completion/error pop-ups
switch the interface between English and Portuguese using a visible selector in the main window
choose the final output directory for structures, JSON report, and execution log
Command Line
Example with PM7 enabled:

python scripts/run_workflow.py --input data/raw/sample_molecules.csv --ph 7.4 --pm7 --pm7-solvent --pm7-eps 78.39
Gas-phase example:

python scripts/run_workflow.py --input data/raw/sample_molecules.csv --no-pm7-solvent
Example with PM7 disabled:

python scripts/run_workflow.py --input data/raw/sample_molecules.csv --no-pm7
Example preserving MOPAC files:

python scripts/run_workflow.py --input data/raw/sample_molecules.csv --preserve-mopac-files
Architecture
SMILES2Docking_Full/
├── AUTHORS.md
├── CITATION.cff
├── LICENSE
├── README.md
├── docs/
├── environment/
├── packaging/
├── config/
├── data/
├── logs/
├── scripts/
├── src/
└── tests/
Environment
Suggested setup:

conda env create -f environment/environment.yml
conda activate smiles2docking
Note: the Windows installer distributed through GitHub Releases already includes the runtime required for desktop use. The Python environment described here is only necessary for development, testing, or generating new builds.

Windows Executable Build
With the smiles2docking environment activated, run:

packaging\windows\build_executable.bat
The build generates a folder in %LOCALAPPDATA%\SMILES2DockingFULLBuild\dist\SMILES2DockingFULL\.

Linux Package Build
On a Linux x86_64 host, with the smiles2docking environment activated:

chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
The process generates:

a portable AppDir
a distributable tar.gz
a tar.gz containing the source code
optionally a .AppImage, if appimagetool is installed
Full details are available in docs/LINUX_DISTRIBUTION.md.

Open Distribution and Notices
Distribution and third-party documents are available in docs/DISTRIBUTION.md and docs/THIRD_PARTY_NOTICES.md.

Project License
This repository is configured for open distribution under GPL-2.0-or-later to maintain compatibility with the use of Open Babel in the distributed application. See LICENSE.

GitHub Publication
The project is published on GitHub with:

source code for the workflow and desktop interface
build scripts for Windows and Linux
project license
citation file
identified authorship
distribution documentation and third-party notices
optional integration with MOPAC for PM7 refinement
Windows installer distributed as a release asset
The Windows installer is available at:


Se quiser, eu também posso aplicar essa tradução diretamente no arquivo [README.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/README.md).


# SMILES2Docking

Aplicativo desktop e workflow Python para preparar ligantes a partir de arquivos `SMI`, `TXT`, `CSV`, `TSV`, `XLS` e `XLSX`, protonar em pH configurável, gerar estruturas 3D, refinar a geometria com `PM7` no `MOPAC` e exportar em `MOL2` ou `SDF`.

## Autoria

- Adriano Marques Gonçalves
- Universidade de Araraquara - UNIARA
- amgoncalves@uniara.edu.br
- Daniel Andrés Grajales Ruiz
- IQ/UNESP
- daniel.g.ruiz@unesp.br

## Principais capacidades

1. Carregar entradas em `SMI`, `TXT`, `CSV`, `TSV`, `XLS` e `XLSX` com ID e SMILES.
2. Remover sais, contraíons e fragmentos desconectados quando o fragmento principal é identificável.
3. Protonar com Open Babel em pH configurável.
4. Gerar estruturas 3D com RDKit.
5. Otimizar geometria com a cascata `MMFF94 -> MMFF94s -> UFF`.
6. Refinar a estrutura final com `MOPAC PM7` usando `MMOK`, `XYZ`, `CHARGE=n` e `EPS=n.nn` opcional.
7. Preservar opcionalmente os arquivos nativos do job do `MOPAC`.
8. Exportar em arquivos `.mol2` separados, em arquivos `.sdf` separados, em um `.mol2` único ou em um `.sdf` único.
9. Gerar relatório JSON com auditoria do processamento.
10. Gerar log final na mesma pasta de saída escolhida.
11. Executar por CLI ou por interface gráfica desktop.

## Download para Windows

Usuários de Windows não precisam instalar Python, MOPAC, Open Babel ou dependências manualmente.

Baixe o instalador na página de releases:

https://github.com/amgoncalvesusp/Smiles2Docking/releases

Arquivo atual:

https://github.com/amgoncalvesusp/Smiles2Docking/releases/download/v1.0/SMILES2DOCKING_Setup_v1.0_win64.exe

Depois de baixar, execute `SMILES2DOCKING_Setup_v1.0_win64.exe` e abra o SMILES2DOCKING pelo menu Iniciar do Windows.

Requisitos:

- Windows 10 64-bit ou superior.
- Nenhuma instalação separada de Python.
- Nenhuma instalação separada de MOPAC.
- Nenhuma instalação separada de Open Babel.

## Estados de protonação

O aplicativo determina o estado de protonação usando o Open Babel no pH selecionado pelo usuário, por meio da etapa `obabel -p <pH>`.

Validação prática desta implementação:

- `CC(=O)O` em `pH 12` foi convertido para `CC(=O)[O-]`
- `CN` em `pH 2` foi convertido para `C[NH3+]`

Isso confirma que a aplicação está ajustando o estado de protonação em função do pH para casos ácido/base simples.

## Refinamento PM7

Quando a etapa PM7 está ativada, o aplicativo:

- calcula a carga líquida final da molécula protonada
- monta um arquivo `.mop` com `PM7 MMOK XYZ CHARGE=n`
- adiciona `EPS=78.39` por padrão para água, com opção de desativar o solvente implícito
- executa o MOPAC e usa a geometria otimizada final para exportação
- pode preservar os arquivos do job do MOPAC em `mopac_files/` dentro do diretório de saída

Busca do binário MOPAC:

1. caminho configurado em `config/settings.yaml`
2. binário empacotado junto com a aplicação
3. `mopac` no `PATH`
4. `C:\Program Files\MOPAC\bin\mopac.exe` no Windows

## Interface gráfica

Execute:

```bash
python scripts/run_gui.py
```

A interface permite:

- selecionar o arquivo de entrada
- escolher a aba Excel
- ajustar as colunas `access_code` e `smiles`
- definir o pH de protonação
- ativar ou desativar o refinamento `PM7`
- ativar ou desativar o solvente implícito com `EPS`
- escolher se os arquivos nativos do `MOPAC` devem ser preservados
- informar manualmente o caminho do executável do `MOPAC`, se necessário
- escolher entre arquivos `MOL2` separados, arquivos `SDF` separados, `MOL2` único ou `SDF` único
- editar o nome base de saída; em exportação separada ele funciona como prefixo opcional
- rodar em segundo plano, minimizando a janela e evitando pop-ups de conclusão/erro
- alternar a interface entre inglês e português por um seletor visível na janela principal
- escolher o diretório final para estruturas, relatório JSON e log de execução

## Linha de comando

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

## Arquitetura

```text
SMILES2Docking_Full/
├── AUTHORS.md
├── CITATION.cff
├── LICENSE
├── README.md
├── docs/
├── environment/
├── packaging/
├── config/
├── data/
├── logs/
├── scripts/
├── src/
└── tests/
```

## Ambiente

Criação sugerida:

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

Observação: o instalador Windows distribuído em GitHub Releases já inclui o runtime necessário para uso desktop. O ambiente Python descrito aqui é necessário apenas para desenvolvimento, testes ou geração de novos builds.

## Build do executável Windows

Use o ambiente `smiles2docking` ativo e rode:

```bash
packaging\windows\build_executable.bat
```

O build gera uma pasta em `%LOCALAPPDATA%\SMILES2DockingFULLBuild\dist\SMILES2DockingFULL\`.

## Build do pacote Linux

Em um host Linux `x86_64`, com o ambiente `smiles2docking` ativo:

```bash
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

O processo gera:

- um `AppDir` portátil
- um `tar.gz` distribuível
- um `tar.gz` com o código-fonte
- opcionalmente um `.AppImage`, se `appimagetool` estiver instalado

Detalhes completos em `docs/LINUX_DISTRIBUTION.md`.

## Distribuição aberta e notices

Os documentos de distribuição e de terceiros estão em `docs/DISTRIBUTION.md` e `docs/THIRD_PARTY_NOTICES.md`.

## Licença do projeto

Este repositório está configurado para distribuição aberta sob `GPL-2.0-or-later`, para manter compatibilidade com o uso do Open Babel na aplicação distribuída. Veja `LICENSE`.

## Publicação no GitHub

O projeto está publicado no GitHub com:

- código-fonte do workflow e da interface desktop
- scripts de build para Windows e Linux
- licença do projeto
- arquivo de citação
- autoria identificada
- documentação de distribuição e notices de terceiros
- integração opcional com MOPAC para refinamento PM7
- instalador Windows distribuído como asset de release

O instalador Windows fica em:

https://github.com/amgoncalvesusp/Smiles2Docking/releases
