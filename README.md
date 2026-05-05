[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19900623.svg)](https://doi.org/10.5281/zenodo.19900623)
# SMILES2Docking

Aplicativo desktop e workflow Python para preparar ligantes a partir de arquivos `SMI`, `TXT`, `CSV`, `TSV`, `XLS` e `XLSX`, protonar em pH configuravel, gerar estruturas 3D, refinar a geometria com `PM7` no `MOPAC` e exportar em `MOL2`, `SDF` ou `PDBQT`.

## Autoria

- Adriano Marques Goncalves
- Universidade de Araraquara - UNIARA
- amgoncalves@uniara.edu.br
- Daniel Andres Grajales Ruiz
- IQ/UNESP
- daniel.g.ruiz@unesp.br
- Nailton Monteiro do Nascimento Junior
- IQ/UNESP

## Principais capacidades

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

## Download para Windows

Usuarios de Windows nao precisam instalar Python, MOPAC, Open Babel ou dependencias manualmente.

Baixe o instalador na pagina de releases:

https://github.com/amgoncalvesusp/Smiles2Docking/releases

Arquivo atual:

https://github.com/amgoncalvesusp/Smiles2Docking/releases/download/v1.1.1/SMILES2DOCKING_Setup_v1.1.1_win64.exe

Depois de baixar, execute `SMILES2DOCKING_Setup_v1.1.1_win64.exe` e abra o SMILES2DOCKING pelo menu Iniciar do Windows.

Requisitos:

- Windows 10 64-bit ou superior.
- Nenhuma instalacao separada de Python.
- Nenhuma instalacao separada de MOPAC.
- Nenhuma instalacao separada de Open Babel.

## Estados de protonacao

O aplicativo determina o estado de protonacao usando o Open Babel no pH selecionado pelo usuario, por meio da etapa `obabel -p <pH>`.

Validacao pratica desta implementacao:

- `CC(=O)O` em `pH 12` foi convertido para `CC(=O)[O-]`
- `CN` em `pH 2` foi convertido para `C[NH3+]`

Isso confirma que a aplicacao esta ajustando o estado de protonacao em funcao do pH para casos acido/base simples.

## Refinamento PM7

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

## Interface grafica

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

## Ambiente

Criacao sugerida:

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

Observacao: o instalador Windows distribuido em GitHub Releases ja inclui o runtime necessario para uso desktop. O ambiente Python descrito aqui e necessario apenas para desenvolvimento, testes ou geracao de novos builds.

## Build do executavel Windows

Use o ambiente `smiles2docking` ativo e rode:

```bash
packaging\windows\build_executable.bat
```

O build gera uma pasta em `%LOCALAPPDATA%\SMILES2DockingBuild\dist\SMILES2Docking\`.

## Build do pacote Linux

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

## Distribuicao aberta e notices

Os documentos de distribuicao e de terceiros estao em `docs/DISTRIBUTION.md` e `docs/THIRD_PARTY_NOTICES.md`.

## Licenca do projeto

Este repositorio esta configurado para distribuicao aberta sob `GPL-2.0-or-later`, para manter compatibilidade com o uso do Open Babel na aplicacao distribuida. Veja `LICENSE`.

## Publicacao no GitHub

O projeto esta publicado no GitHub com:

- codigo-fonte do workflow e da interface desktop
- scripts de build para Windows e Linux
- licenca do projeto
- arquivo de citacao
- autoria identificada
- documentacao de distribuicao e notices de terceiros
- integracao opcional com MOPAC para refinamento PM7
- instalador Windows distribuido como asset de release

O instalador Windows fica em:

https://github.com/amgoncalvesusp/Smiles2Docking/releases
