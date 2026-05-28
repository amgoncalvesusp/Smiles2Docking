# SMILES2Docking

**[English](#english) | [Português](#português)**

---

## English

Desktop application and Python workflow for preparing ligands from `CSV`, `XLS`, and `XLSX` spreadsheets. The pipeline performs structural curation, multi-site protonation at configurable pH, 3D generation with `RDKit ETKDGv3`, force-field geometry optimization (`MMFF94 → MMFF94s → UFF`), optional semi-empirical refinement with `MOPAC PM7`, and exports in `MOL2`, `SDF`, or `PDBQT` format ready for `AutoDock Vina`.

### Authors

- Adriano Marques Gonçalves — Universidade de Araraquara (UNIARA) — amgoncalves@uniara.edu.br
- Daniel Grajales Ruiz — Universidade Estadual Paulista (UNESP)
- Nailton Monteiro do Nascimento Júnior — Universidade Estadual Paulista (UNESP)

### Key capabilities

1. Load spreadsheets with ID and SMILES columns.
2. Remove salts, counter-ions, and disconnected fragments when the principal fragment is identifiable.
3. Protonate with a selectable backend (`Dimorphite-DL`, `Open Babel`, or none) at configurable pH, with multi-site treatment and context-aware pKa rules.
4. Generate 3D structures with `RDKit ETKDGv3`.
5. Optimize geometry with the `MMFF94 → MMFF94s → UFF` force-field cascade.
6. Optional semi-empirical refinement via `MOPAC PM7` (`PM6`, `PM6-D3H4X`, `PM6-ORG`, `RM1`, `PM3`, `AM1`, `MNDO` also supported); disabled by default to preserve throughput.
7. Export in `MOL2`, `SDF`, or `PDBQT` (the latter via `Meeko`, avoiding the fragmentation observed in `Open Babel`-only converters), in `separate_*` or `single_*` modes.
8. Parallelization via `joblib` configurable by `n_jobs`, with isolated workers that inherit only the serializable configuration dictionary.
9. Per-run JSON report including per-molecule timings, stage breakdown (`clean`, `protonate`, `build_3d`, `export`), mean/median/p95, fastest/slowest, wall-clock, and throughput in molecules per minute.
10. Final log written to the chosen output folder.
11. Execution via CLI, desktop GUI, or distributable package (Windows `.exe`, Linux `AppImage`).

### Protonation backends

Configurable in `config/settings.yaml` under `protonation.backend`:

| Backend | When to use | Notes |
|---------|-------------|-------|
| `dimorphite` (default) | Multi-site curation with context-aware pKa rules | Recognizes substituent effects, neighboring groups, and multiple ionizable centers. Output controlled by `ph`, `ph_tolerance`, `max_variants`, `variant_selection`. |
| `openbabel` | Compatibility with legacy pipelines or when `Dimorphite-DL` is unavailable | Applies `obabel -p <pH>`; less accurate for molecules with multiple ionizable centers. |
| `none` | Diagnostics or when input is already protonated | Pass-through; keeps input SMILES unchanged. |

Practical validation with `Dimorphite-DL`:

- `CC(=O)O` at `pH 12` is converted to `CC(=O)[O-]`
- `CN` at `pH 2` is converted to `C[NH3+]`
- Diamines such as `NCCCCN` at `pH 7.4` receive selective protonation according to local pKa, avoiding the duplicate protonation typical of `Open Babel`'s `-p` flag.

### Parallelization and scalability

Configurable in `config/settings.yaml` under the `parallel` section:

```yaml
parallel:
  enabled: true
  n_jobs: -1        # -1 => all cores; 1 => sequential
  backend: loky
  batch_size: auto
```

The throughput benchmark is available at [scripts/benchmark.py](scripts/benchmark.py):

```bash
python scripts/benchmark.py --input data/raw/zinc_sample.csv --sizes 100 1000 --jobs 1 4 8
```

The script writes a CSV to `data/reports/benchmark_<timestamp>.csv` with absolute times, throughput, and stage breakdown.

### Optional semi-empirical refinement (MOPAC)

Disabled by default. To enable:

```yaml
structure_generation:
  mopac:
    enabled: true
    method: PM7
    binary: mopac
    keywords: "PM7 PRECISE GNORM=0.01"
    max_seconds: 120
```

Refinement is applied after the force-field cascade. If the MOPAC executable fails, the pipeline keeps the force-field geometry and records `mopac_status=failed` in the molecule record and the run report.

### Graphical interface

Run:

```bash
python scripts/run_gui.py
```

The interface allows you to:

- select the input file
- choose the Excel sheet
- configure the `access_code` and `smiles` columns
- set the protonation pH
- choose between separate `MOL2`, separate `SDF`, single `MOL2`, single `SDF`, separate `PDBQT`, or single `PDBQT`
- set the output base name (used as prefix in separate-file modes)
- run in the background, minimizing the window and suppressing completion/error pop-ups
- switch the interface language between English and Portuguese via a selector in the main window
- choose the output directory for structures, JSON report, and execution log

### Command line

Example with Excel:

```bash
python scripts/run_workflow.py --input data/raw/molecules.xlsx --sheet Molecules --ph 7.4
```

Example with CSV:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --smiles-column smiles --access-code-column access_code --ph 6.8
```

Example with single-file SDF export:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --export-mode single_sdf --output-name ligands_pH68
```

Example with PDBQT export ready for `AutoDock Vina`:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --export-mode separate_pdbqt --ph 7.4
```

### Output directories

When `output_dir`, `temp_dir`, and `report_dir` in `config/settings.yaml` are left blank, the pipeline automatically resolves to the OS user data directory:

| OS | Path |
|----|------|
| Windows | `%APPDATA%\smiles2docking\` |
| Linux | `$XDG_DATA_HOME/smiles2docking/` (default `~/.local/share/smiles2docking/`) |
| macOS | `~/Library/Application Support/smiles2docking/` |

This prevents failures in read-only distributions such as `AppImage`.

### Project layout

```text
SMILES2Docking/
├── AUTHORS.md
├── CITATION.cff
├── LICENSE
├── README.md
├── config/
├── data/
├── docs/
├── environment/
├── packaging/
├── scripts/
├── src/
└── tests/
```

### Environment setup

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

### Windows executable build

With the `smiles2docking` environment active:

```bash
packaging\windows\build_executable.bat
```

Generates a distributable folder at `dist/SMILES2DockingDesktop/`.

### Linux AppImage build

On a Linux `x86_64` host with the `smiles2docking` environment active:

```bash
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

Produces a portable `AppDir`, a distributable `tar.gz`, and optionally an `.AppImage` if `appimagetool` is installed. See [docs/LINUX_DISTRIBUTION.md](docs/LINUX_DISTRIBUTION.md) for full details.

### License

GPL-2.0-or-later — see [LICENSE](LICENSE).

### Citation

If you use SMILES2Docking in published research, please cite it using the metadata in [CITATION.cff](CITATION.cff).

---

## Português

Aplicativo desktop e workflow Python para preparar ligantes a partir de planilhas `CSV`, `XLS` e `XLSX`. O pipeline executa curadoria estrutural, protonação multi-sítio em pH configurável, geração 3D com `RDKit ETKDGv3`, refinamento por campos de força (`MMFF94 → MMFF94s → UFF`), refinamento semi-empírico opcional `MOPAC PM7` e exporta em `MOL2`, `SDF` ou `PDBQT` pronto para `AutoDock Vina`.

### Autoria

- Adriano Marques Gonçalves — Universidade de Araraquara (UNIARA) — amgoncalves@uniara.edu.br
- Daniel Grajales Ruiz — Universidade Estadual Paulista (UNESP)

### Principais capacidades

1. Carregar planilhas com colunas de ID e SMILES.
2. Remover sais, contraíons e fragmentos desconectados quando o fragmento principal é identificável.
3. Protonar com backend selecionável (`Dimorphite-DL`, `Open Babel` ou nenhum) em pH configurável, com tratamento multi-sítio e regras de pKa por contexto químico.
4. Gerar estruturas 3D com `RDKit ETKDGv3`.
5. Otimizar geometria com a cascata `MMFF94 → MMFF94s → UFF`.
6. Refinamento semi-empírico opcional via `MOPAC PM7` (`PM6`, `PM6-D3H4X`, `PM6-ORG`, `RM1`, `PM3`, `AM1`, `MNDO` também suportados), desativado por padrão para preservar throughput.
7. Exportação em `MOL2`, `SDF` ou `PDBQT` (este último via `Meeko`, evitando a fragmentação observada em conversores baseados apenas em `Open Babel`), nos modos `separate_*` ou `single_*`.
8. Paralelização por `joblib` configurável por `n_jobs`, com workers isolados que herdam apenas o dicionário de configuração serializável.
9. Relatório JSON por execução incluindo tempos por molécula, estágios (`clean`, `protonate`, `build_3d`, `export`), média/mediana/p95, fastest/slowest, wall-clock e throughput em moléculas por minuto.
10. Log final na pasta de saída escolhida.
11. Execução por CLI, interface gráfica desktop ou pacote distribuível (Windows `.exe`, Linux `AppImage`).

### Backends de protonação

Configurável em `config/settings.yaml` no campo `protonation.backend`:

| Backend | Quando usar | Observações |
|---------|-------------|-------------|
| `dimorphite` (padrão) | Curadoria multi-sítio com regras de pKa contextuais | Reconhece efeitos de substituintes, vizinhança e múltiplos centros ionizáveis. Saída controlada por `ph`, `ph_tolerance`, `max_variants`, `variant_selection`. |
| `openbabel` | Compatibilidade com pipelines legados ou ausência de `Dimorphite-DL` | Aplica `obabel -p <pH>`; menos preciso em moléculas com vários centros ionizáveis. |
| `none` | Diagnóstico ou quando a entrada já está protonada | Pass-through, mantém o SMILES de entrada. |

Validação prática com `Dimorphite-DL`:

- `CC(=O)O` em `pH 12` é convertido para `CC(=O)[O-]`
- `CN` em `pH 2` é convertido para `C[NH3+]`
- Diaminas como `NCCCCN` em `pH 7.4` recebem protonação seletiva conforme o pKa local, evitando a protonação duplicada característica do modo `-p` do Open Babel.

### Paralelização e escalabilidade

Configurável em `config/settings.yaml` na seção `parallel`:

```yaml
parallel:
  enabled: true
  n_jobs: -1        # -1 => todos os núcleos; 1 => sequencial
  backend: loky
  batch_size: auto
```

O benchmark de throughput está disponível em [scripts/benchmark.py](scripts/benchmark.py):

```bash
python scripts/benchmark.py --input data/raw/zinc_sample.csv --sizes 100 1000 --jobs 1 4 8
```

O script gera CSV em `data/reports/benchmark_<timestamp>.csv` com tempos absolutos, throughput e estágio.

### Refinamento semi-empírico opcional (MOPAC)

Desativado por padrão. Para ativar:

```yaml
structure_generation:
  mopac:
    enabled: true
    method: PM7
    binary: mopac
    keywords: "PM7 PRECISE GNORM=0.01"
    max_seconds: 120
```

O refinamento é aplicado após a cascata de campo de força. Em caso de falha do executável, o pipeline mantém a geometria do campo de força e registra `mopac_status=failed` na molécula e no relatório.

### Interface gráfica

Execute:

```bash
python scripts/run_gui.py
```

A interface permite:

- selecionar o arquivo de entrada
- escolher a aba Excel
- ajustar as colunas `access_code` e `smiles`
- definir o pH de protonação
- escolher entre arquivos `MOL2` separados, arquivos `SDF` separados, `MOL2` único, `SDF` único, `PDBQT` separados ou `PDBQT` único
- editar o nome base de saída; em exportação separada ele funciona como prefixo opcional
- rodar em segundo plano, minimizando a janela e evitando pop-ups de conclusão/erro
- alternar a interface entre inglês e português por um seletor visível na janela principal
- escolher o diretório final para estruturas, relatório JSON e log de execução

### Linha de comando

Exemplo com Excel:

```bash
python scripts/run_workflow.py --input data/raw/molecules.xlsx --sheet Molecules --ph 7.4
```

Exemplo com CSV:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --smiles-column smiles --access-code-column access_code --ph 6.8
```

Exemplo com exportação em arquivo único SDF:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --export-mode single_sdf --output-name ligands_pH68
```

Exemplo com exportação PDBQT pronta para `AutoDock Vina`:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --export-mode separate_pdbqt --ph 7.4
```

### Diretórios de execução

Quando os campos `output_dir`, `temp_dir` e `report_dir` em `config/settings.yaml` estão vazios, o pipeline resolve automaticamente para o diretório de dados do usuário do sistema operacional:

| SO | Caminho |
|----|---------|
| Windows | `%APPDATA%\smiles2docking\` |
| Linux | `$XDG_DATA_HOME/smiles2docking/` (padrão `~/.local/share/smiles2docking/`) |
| macOS | `~/Library/Application Support/smiles2docking/` |

Isso evita falhas em distribuições somente leitura, como o `AppImage`.

### Estrutura do projeto

```text
SMILES2Docking/
├── AUTHORS.md
├── CITATION.cff
├── LICENSE
├── README.md
├── config/
├── data/
├── docs/
├── environment/
├── packaging/
├── scripts/
├── src/
└── tests/
```

### Configuração do ambiente

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

### Build do executável Windows

Com o ambiente `smiles2docking` ativo:

```bash
packaging\windows\build_executable.bat
```

Gera uma pasta distribuível em `dist/SMILES2DockingDesktop/`.

### Build do pacote Linux

Em um host Linux `x86_64` com o ambiente `smiles2docking` ativo:

```bash
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

Gera um `AppDir` portátil, um `tar.gz` distribuível e opcionalmente um `.AppImage`, se `appimagetool` estiver instalado. Detalhes em [docs/LINUX_DISTRIBUTION.md](docs/LINUX_DISTRIBUTION.md).

### Licença

GPL-2.0-or-later — veja [LICENSE](LICENSE).

### Citação

Se você usar o SMILES2Docking em pesquisa publicada, por favor cite usando os metadados em [CITATION.cff](CITATION.cff).
