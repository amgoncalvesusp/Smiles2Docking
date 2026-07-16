from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.app_metadata import (
    APP_NAME,
    APP_VERSION,
    AUTHOR_EMAIL,
    AUTHOR_SUMMARY,
    PROJECT_LICENSE,
)
from src.quantum.mopac_methods import (
    COMMON_MOPAC_METHODS,
    get_method_info,
    normalize_mopac_method,
)
from src.utils.config import (
    default_path_for_display,
    load_settings,
    merge_settings,
    resolve_project_path,
    resolve_settings_paths,
)
from src.utils.logging_utils import setup_logging
from src.workflow.pipeline import run_workflow


SKIP_UNDEFINED_STEREO_EXPLANATION = (
    "Use this option when you want to test only molecules with fully defined stereochemistry.\n"
    " This is recommended for more restrictive virtual screening workflows where stereochemical\n"
    " ambiguity could lead to unreliable docking poses. Molecules with undefined chiral centers\n"
    " will be skipped entirely. Note: for nitrogen atoms, only those that become asymmetric\n"
    " upon protonation are evaluated — unprotonated nitrogens with undefined geometry are ignored."
)


LANGUAGE_TEXT = {
    "en": {
        "about": "About",
        "title": "Ligand preparation with MOPAC refinement",
        "subtitle": "Load a spreadsheet, adjust protonation pH, refine the final 3D structure with a selectable MOPAC method, and export MOL2 or SDF files without blocking the desktop.",
        "input": "Input",
        "processing": "Processing",
        "output": "Output",
        "execution": "Execution",
        "language": "Language",
        "file": "Input file",
        "sheet": "Excel sheet",
        "smiles": "SMILES column",
        "id": "ID column",
        "ph": "Target pH",
        "protonation_backend": "Protonation tool",
        "protonation_backend_hint": "MolGpKa predicts the dominant protonation state via a GNN pKa model (recommended). Dimorphite-DL (all states) enumerates every plausible state; (single) picks one. Open Babel uses the legacy -p mode. None disables protonation.",
        "tautomer": "Dominant tautomer",
        "tautomer_backend": "Tautomer ranking",
        "tautomer_hint": "Optional and off by default. When enabled, the dominant (lowest-energy) tautomer is selected before protonation, and the protonation backend then runs on it. RDKit uses its canonical tautomer (bundled). sPhysNet-Taut is an external tool you install separately (Linux only; on Windows run under WSL).",
        "tautomer_script": "sPhysNet-Taut script",
        "tautomer_script_hint": "Path to predict_tautomer.py from the cloned sPhysNet-Taut repository.",
        "tautomer_python": "sPhysNet-Taut env python",
        "tautomer_python_hint": "Python executable of the conda env where sPhysNet-Taut is installed (leave blank to use 'python').",
        "skip_undefined_stereo": "Skip undefined stereochemistry",
        "strict_stereo": "Enumerate undefined stereochemistry",
        "strict_stereo_single_only": "Only when exactly one center is undefined",
        "strict_stereo_single_hint": "Recommended for very large databases: molecules with two or more undefined tetrahedral centers are flagged in the final report and skipped.",
        "pm7": "Enable MOPAC refinement",
        "mopac_method": "MOPAC method",
        "mopac_method_hint": "PM7 remains the default. You can select a suggested method or type another valid MOPAC keyword.",
        "pm7_solvent": "Use water dielectric (COSMO EPS)",
        "pm7_eps": "Dielectric constant (EPS)",
        "pm7_preserve": "Preserve MOPAC files",
        "pm7_preserve_hint": "Copies .mop, .out, .arc and related job files to an output subfolder named mopac_files.",
        "mopac_binary": "MOPAC executable",
        "mopac_binary_hint": "Optional. Leave blank to auto-detect MOPAC in the bundled app, PATH, or the default system location.",
        "output_dir": "Output directory",
        "export_mode": "Export mode",
        "bundle_name": "Output name / prefix",
        "report_enabled": "Write JSON audit report",
        "report_dir": "Report directory",
        "report_hint": "A single JSON report is written per run, with one entry per compound. Disable it to skip report writing for very large batches.",
        "bundle_hint_single": "Used as the name of the single exported file.",
        "bundle_hint_separate": "Optional prefix for separate files. Leave blank to keep only the compound IDs.",
        "browse": "Browse...",
        "browse_input_title": "Select spreadsheet",
        "browse_output_title": "Select output directory",
        "browse_mopac_title": "Select MOPAC executable",
        "spreadsheet_filter": "Input files (*.smi *.txt *.csv *.tsv *.xls *.xlsx)",
        "executable_filter": "Executables (*.exe);;All files (*)",
        "run": "Run workflow",
        "clear_log": "Clear log",
        "sheet_placeholder": "Optional for Excel",
        "log_placeholder": "Execution log will appear here.",
        "status_idle": "Waiting to start.",
        "status_initializing": "Initializing workflow...",
        "status_completed": "Execution completed.",
        "status_failed": "Execution failed.",
        "warning_input": "Select a SMI/TXT/CSV/TSV/XLS/XLSX input file.",
        "summary_author": f"Authors: {AUTHOR_SUMMARY} | Contact: {AUTHOR_EMAIL}",
        "mode_separate_mol2": "Separate MOL2 files",
        "mode_separate_sdf": "Separate SDF files",
        "mode_separate_pdbqt": "Separate PDBQT files",
        "mode_single_mol2": "Single MOL2 file",
        "mode_single_sdf": "Single SDF file",
        "mode_single_pdbqt": "Single PDBQT file",
        "background": "Run in background and minimize the window",
        "failure_summary": "Execution failed: {message}",
        "author_label": "Author",
        "license_label": "Project license",
        "summary_status": "Status",
        "summary_ph": "pH",
        "summary_pm7": "MOPAC",
        "summary_eps": "EPS",
        "summary_pm7_files": "MOPAC files",
        "summary_export": "Export",
        "summary_records": "Structures exported",
        "summary_files": "Files generated",
        "summary_stereo": "Stereo issues",
        "summary_enumerated": "enumerated",
        "summary_skipped": "skipped",
        "summary_failures": "Failures/skipped",
        "summary_report": "Report",
        "summary_log": "Final log",
        "about_title": f"About {APP_NAME}",
        "about_notice": "Open distribution with third-party notices in docs/THIRD_PARTY_NOTICES.md. MOPAC refinement uses PM7 by default and can run other supported methods.",
        "bundle_placeholder_enabled": "Example: prepared_ligands",
        "bundle_placeholder_disabled": "Optional prefix for separate-file export",
        "pm7_disabled": "Disabled",
        "pm7_enabled_summary": "{method} ({count} optimized)",
        "gas_phase": "Gas phase",
    },
    "pt": {
        "about": "Sobre",
        "title": "Preparação de ligantes com refinamento PM7",
        "subtitle": "Carregue uma planilha, ajuste o pH de protonação, refine a estrutura 3D final com MOPAC PM7 e exporte arquivos MOL2 ou SDF sem bloquear o desktop.",
        "input": "Entrada",
        "processing": "Processamento",
        "output": "Saída",
        "execution": "Execução",
        "language": "Idioma",
        "file": "Arquivo de entrada",
        "sheet": "Aba Excel",
        "smiles": "Coluna SMILES",
        "id": "Coluna ID",
        "ph": "pH alvo",
        "protonation_backend": "Ferramenta de protonacao",
        "protonation_backend_hint": "MolGpKa preve o estado de protonacao dominante via modelo GNN de pKa (recomendado). Dimorphite-DL (todos os estados) enumera cada estado plausivel; (unico) escolhe um. Open Babel usa o modo legado -p. Nenhuma desativa a protonacao.",
        "tautomer": "Tautomero dominante",
        "tautomer_backend": "Ranqueamento de tautomeros",
        "tautomer_hint": "Opcional e desativado por padrao. Quando ativado, o tautomero dominante (de menor energia) e selecionado antes da protonacao, e o backend de protonacao roda sobre ele. RDKit usa seu tautomero canonico (embutido). sPhysNet-Taut e uma ferramenta externa instalada separadamente (apenas Linux; no Windows, use WSL).",
        "tautomer_script": "Script sPhysNet-Taut",
        "tautomer_script_hint": "Caminho para predict_tautomer.py do repositorio sPhysNet-Taut clonado.",
        "tautomer_python": "Python do env sPhysNet-Taut",
        "tautomer_python_hint": "Executavel python do env conda onde o sPhysNet-Taut esta instalado (deixe vazio para usar 'python').",
        "skip_undefined_stereo": "Ignorar estereoquimica indefinida",
        "strict_stereo": "Enumerar estereoquimica indefinida",
        "strict_stereo_single_only": "Apenas quando exatamente um centro estiver indefinido",
        "strict_stereo_single_hint": "Recomendado para bancos muito grandes: moleculas com dois ou mais centros tetraedricos indefinidos entram no relatorio final e sao ignoradas.",
        "pm7": "Ativar refinamento MOPAC",
        "mopac_method": "Metodo do MOPAC",
        "mopac_method_hint": "PM7 continua como padrao. Voce pode selecionar um metodo sugerido ou digitar outra keyword valida do MOPAC.",
        "pm7_solvent": "Usar dielétrico da água (COSMO EPS)",
        "pm7_eps": "Constante dielétrica (EPS)",
        "pm7_preserve": "Preservar arquivos do MOPAC",
        "pm7_preserve_hint": "Copia .mop, .out, .arc e arquivos relacionados do job para uma subpasta de saída chamada mopac_files.",
        "mopac_binary": "Executável do MOPAC",
        "mopac_binary_hint": "Opcional. Deixe em branco para detectar o MOPAC no app empacotado, no PATH ou no local padrão do sistema.",
        "output_dir": "Diretório de saída",
        "export_mode": "Modo de exportação",
        "bundle_name": "Nome de saída / prefixo",
        "report_enabled": "Gravar relatorio JSON de auditoria",
        "report_dir": "Diretorio do relatorio",
        "report_hint": "Um unico relatorio JSON e gravado por execucao, com uma entrada por composto. Desative para pular a gravacao em lotes muito grandes.",
        "bundle_hint_single": "Usado como nome do arquivo único exportado.",
        "bundle_hint_separate": "Prefixo opcional para arquivos separados. Deixe em branco para usar apenas os IDs.",
        "browse": "Selecionar...",
        "browse_input_title": "Selecionar planilha",
        "browse_output_title": "Selecionar diretório de saída",
        "browse_mopac_title": "Selecionar executável do MOPAC",
        "spreadsheet_filter": "Arquivos de entrada (*.smi *.txt *.csv *.tsv *.xls *.xlsx)",
        "executable_filter": "Executáveis (*.exe);;Todos os arquivos (*)",
        "run": "Executar workflow",
        "clear_log": "Limpar log",
        "sheet_placeholder": "Opcional para Excel",
        "log_placeholder": "O log de execução aparecerá aqui.",
        "status_idle": "Aguardando execução.",
        "status_initializing": "Inicializando workflow...",
        "status_completed": "Execução concluída.",
        "status_failed": "Execução falhou.",
        "warning_input": "Selecione um arquivo SMI/TXT/CSV/TSV/XLS/XLSX.",
        "summary_author": f"Autoria: {AUTHOR_SUMMARY} | Contato: {AUTHOR_EMAIL}",
        "mode_separate_mol2": "Arquivos MOL2 separados",
        "mode_separate_sdf": "Arquivos SDF separados",
        "mode_separate_pdbqt": "Arquivos PDBQT separados",
        "mode_single_mol2": "Um único arquivo MOL2",
        "mode_single_sdf": "Um único arquivo SDF",
        "mode_single_pdbqt": "Um único arquivo PDBQT",
        "background": "Executar em segundo plano e minimizar a janela",
        "failure_summary": "Execução falhou: {message}",
        "author_label": "Autoria",
        "license_label": "Licença do projeto",
        "summary_status": "Status",
        "summary_ph": "pH",
        "summary_pm7": "MOPAC",
        "summary_eps": "EPS",
        "summary_pm7_files": "Arquivos MOPAC",
        "summary_export": "Exportação",
        "summary_records": "Estruturas exportadas",
        "summary_files": "Arquivos gerados",
        "summary_stereo": "Problemas estereoquimicos",
        "summary_enumerated": "enumeradas",
        "summary_skipped": "ignoradas",
        "summary_failures": "Falhas/ignorados",
        "summary_report": "Relatório",
        "summary_log": "Log final",
        "about_title": f"Sobre {APP_NAME}",
        "about_notice": "Distribuição aberta com notices de terceiros em docs/THIRD_PARTY_NOTICES.md. O refinamento PM7 usa MOPAC quando disponível.",
        "bundle_placeholder_enabled": "Ex.: prepared_ligands",
        "bundle_placeholder_disabled": "Prefixo opcional para exportação em arquivos separados",
        "pm7_disabled": "Desativado",
        "pm7_enabled_summary": "{method} ({count} otimizadas)",
        "gas_phase": "Fase gasosa",
    },
}


@dataclass(slots=True)
class WorkflowOverrides:
    input_file: str
    sheet_name: str
    smiles_column: str
    access_code_column: str
    output_dir: str
    export_mode: str
    bundle_basename: str
    ph: float
    protonation_backend: str
    skip_undefined_stereo: bool
    strict_stereochemistry: bool
    single_undefined_stereocenter_only: bool
    pm7_enabled: bool
    mopac_method: str
    pm7_use_eps: bool
    pm7_eps: float
    pm7_preserve_files: bool
    mopac_binary: str
    run_in_background: bool
    tautomer_enabled: bool
    tautomer_backend: str
    tautomer_script: str
    tautomer_python: str
    report_enabled: bool
    report_dir: str


class WorkflowWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)
    log_message = Signal(str)
    progress_changed = Signal(int, int, str)

    def __init__(self, settings: dict) -> None:
        super().__init__()
        self.settings = settings

    def run(self) -> None:
        try:
            logger = setup_logging(self.settings)
            result = run_workflow(
                self.settings,
                logger=logger,
                progress_callback=self.progress_changed.emit,
                message_callback=self.log_message.emit,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.finished.emit(
            {
                "status": result.report.status,
                "report_path": result.report_path,
                "structure_files_written": result.report.structure_files_written,
                "structure_records_exported": result.report.structure_records_exported,
                "export_mode": result.report.export_mode,
                "export_format": result.report.export_format,
                "pm7_enabled": result.report.pm7_enabled,
                "pm7_method": result.report.pm7_method,
                "pm7_solvent_eps": result.report.pm7_solvent_eps,
                "pm7_optimized": result.report.molecules_optimized_with_pm7,
                "pm7_files_preserved": result.report.pm7_files_preserved,
                "pm7_preserved_file_count": result.report.pm7_preserved_file_count,
                "pm7_preserved_files_dir": result.report.pm7_preserved_files_dir or "",
                "failures": result.report.failures_or_skipped_entries,
                "stereochemistry_issues": result.report.records_with_undefined_stereochemistry,
                "stereochemistry_enumerated": result.report.stereochemistry_records_enumerated,
                "stereochemistry_skipped": result.report.stereochemistry_records_skipped,
                "ph": result.report.protonation_ph,
                "log_file_path": result.report.log_file_path or "",
            }
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.base_settings = load_settings()
        self.current_language = self.base_settings.get("ui", {}).get("language", "en")
        if self.current_language not in LANGUAGE_TEXT:
            self.current_language = "en"
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1024, 680)
        self.setMinimumSize(860, 600)
        self._thread: QThread | None = None
        self._worker: WorkflowWorker | None = None
        self._last_payload: dict | None = None
        self._form_layouts: list[QFormLayout] = []

        self._build_menu()
        self._build_ui()
        self._apply_style()
        self._apply_language()
        self._update_responsive_layout(self.width())

    def _text(self, key: str) -> str:
        return LANGUAGE_TEXT[self.current_language][key]

    def _apply_language(self) -> None:
        self.language_label.setText(self._text("language"))
        self.about_button.setText(self._text("about"))
        self.header.setText(self._text("title"))
        self.subtitle.setText(self._text("subtitle"))
        self.input_group.setTitle(self._text("input"))
        self.processing_group.setTitle(self._text("processing"))
        self.output_group.setTitle(self._text("output"))
        self.execution_group.setTitle(self._text("execution"))
        self.input_file_label.setText(self._text("file"))
        self.sheet_label.setText(self._text("sheet"))
        self.smiles_label.setText(self._text("smiles"))
        self.id_label.setText(self._text("id"))
        self.ph_label.setText(self._text("ph"))
        self.protonation_backend_label.setText(self._text("protonation_backend"))
        self.protonation_backend_hint_label.setText(
            self._text("protonation_backend_hint")
        )
        self.tautomer_label.setText(self._text("tautomer"))
        self.tautomer_backend_label.setText(self._text("tautomer_backend"))
        self.tautomer_hint_label.setText(self._text("tautomer_hint"))
        self.tautomer_script_label.setText(self._text("tautomer_script"))
        self.tautomer_script_hint_label.setText(self._text("tautomer_script_hint"))
        self.tautomer_python_label.setText(self._text("tautomer_python"))
        self.tautomer_python_hint_label.setText(self._text("tautomer_python_hint"))
        self.browse_tautomer_script_button.setText(self._text("browse"))
        self.browse_tautomer_python_button.setText(self._text("browse"))
        self.skip_undefined_stereo_label.setText(self._text("skip_undefined_stereo"))
        self.skip_undefined_stereo_hint_label.setText(SKIP_UNDEFINED_STEREO_EXPLANATION)
        self.strict_stereo_label.setText(self._text("strict_stereo"))
        self.single_undefined_stereo_label.setText(
            self._text("strict_stereo_single_only")
        )
        self.single_undefined_stereo_hint_label.setText(
            self._text("strict_stereo_single_hint")
        )
        self.pm7_label.setText(self._text("pm7"))
        self.mopac_method_label.setText(self._text("mopac_method"))
        self.mopac_method_hint_label.setText(self._text("mopac_method_hint"))
        self.pm7_solvent_label.setText(self._text("pm7_solvent"))
        self.pm7_eps_label.setText(self._text("pm7_eps"))
        self.pm7_preserve_label.setText(self._text("pm7_preserve"))
        self.pm7_preserve_hint_label.setText(self._text("pm7_preserve_hint"))
        self.mopac_binary_label.setText(self._text("mopac_binary"))
        self.mopac_binary_hint_label.setText(self._text("mopac_binary_hint"))
        self.output_dir_label.setText(self._text("output_dir"))
        self.report_enabled_label.setText(self._text("report_enabled"))
        self.report_dir_label.setText(self._text("report_dir"))
        self.report_hint_label.setText(self._text("report_hint"))
        self.browse_report_button.setText(self._text("browse"))
        self.export_mode_label.setText(self._text("export_mode"))
        self.bundle_name_label.setText(self._text("bundle_name"))
        self.bundle_name_hint_label.setText(self._bundle_name_hint_text())
        self.browse_input_button.setText(self._text("browse"))
        self.browse_output_button.setText(self._text("browse"))
        self.browse_mopac_button.setText(self._text("browse"))
        self.run_button.setText(self._text("run"))
        self.clear_log_button.setText(self._text("clear_log"))
        self.run_in_background_checkbox.setText(self._text("background"))
        self.pm7_checkbox.setText("")
        self.pm7_solvent_checkbox.setText("")
        self.sheet_edit.setPlaceholderText(self._text("sheet_placeholder"))
        self.log_box.setPlaceholderText(self._text("log_placeholder"))
        self.progress_label.setText(self._text("status_idle"))
        self.summary_label.setText(self._text("summary_author"))
        self._refresh_export_mode_labels()
        self._update_mopac_method_description()
        self._toggle_bundle_name_state()
        self._toggle_stereochemistry_state()
        self._toggle_pm7_state()
        if self._last_payload is not None:
            self._set_summary(self._last_payload)

    def _refresh_export_mode_labels(self) -> None:
        label_map = {
            "separate_mol2": self._text("mode_separate_mol2"),
            "separate_sdf": self._text("mode_separate_sdf"),
            "separate_pdbqt": self._text("mode_separate_pdbqt"),
            "single_mol2": self._text("mode_single_mol2"),
            "single_sdf": self._text("mode_single_sdf"),
            "single_pdbqt": self._text("mode_single_pdbqt"),
        }
        for index in range(self.export_mode_combo.count()):
            export_mode = str(self.export_mode_combo.itemData(index))
            self.export_mode_combo.setItemText(
                index, label_map.get(export_mode, export_mode)
            )

    def _change_language(self) -> None:
        selected = str(self.language_combo.currentData())
        if selected in LANGUAGE_TEXT and selected != self.current_language:
            self.current_language = selected
            self._apply_language()

    def _build_menu(self) -> None:
        menu_container = QWidget(self)
        menu_layout = QHBoxLayout(menu_container)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(12)

        app_badge = QLabel(APP_NAME, menu_container)
        app_badge.setObjectName("menuBadge")
        self.menu_badge = app_badge

        self.language_label = QLabel(self._text("language"), menu_container)
        self.language_label.setObjectName("toolbarLabel")
        self.language_combo = QComboBox(menu_container)
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Português", "pt")
        self.language_combo.setCurrentIndex(
            max(self.language_combo.findData(self.current_language), 0)
        )
        self.language_combo.currentIndexChanged.connect(self._change_language)

        about_button = QPushButton("Sobre", menu_container)
        about_button.setObjectName("menuButton")
        about_button.clicked.connect(self._show_about_dialog)
        self.about_button = about_button

        menu_layout.addWidget(app_badge)
        menu_layout.addStretch(1)
        menu_layout.addWidget(self.language_label, 0, Qt.AlignVCenter)
        menu_layout.addWidget(self.language_combo, 0, Qt.AlignVCenter)
        menu_layout.addWidget(about_button, 0, Qt.AlignVCenter)

        self.top_bar = menu_container

    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("centralSurface")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(central)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_content.setObjectName("centralSurface")
        scroll_area.setWidget(scroll_content)

        self.main_layout = QBoxLayout(QBoxLayout.LeftToRight, scroll_content)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(16)

        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(14)
        self.main_layout.addLayout(controls_layout, 4)

        side_layout = QVBoxLayout()
        side_layout.setSpacing(14)
        self.main_layout.addLayout(side_layout, 5)

        controls_layout.addWidget(self.top_bar)

        header = QLabel(self._text("title"))
        self.header = header
        header.setObjectName("heroTitle")
        subtitle = QLabel(self._text("subtitle"))
        self.subtitle = subtitle
        subtitle.setWordWrap(True)
        subtitle.setObjectName("heroSubtitle")

        controls_layout.addWidget(header)
        controls_layout.addWidget(subtitle)

        controls_layout.addWidget(self._build_input_group())
        controls_layout.addWidget(self._build_processing_group())
        controls_layout.addWidget(self._build_output_group())
        controls_layout.addStretch(1)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText(self._text("log_placeholder"))
        self.log_box.setMinimumHeight(240)

        self.progress_label = QLabel(self._text("status_idle"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.summary_label = QLabel(self._text("summary_author"))
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("summaryLabel")

        side_layout.addWidget(self._build_actions_group())
        side_layout.addWidget(self.progress_label)
        side_layout.addWidget(self.progress_bar)
        side_layout.addWidget(self.log_box, 1)
        side_layout.addWidget(self.summary_label)

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox(self._text("input"))
        self.input_group = group
        layout = QFormLayout(group)
        self._configure_form_layout(layout)

        input_defaults = self.base_settings["input"]
        default_input = input_defaults.get("file_path") or str(
            resolve_project_path("data/raw/sample_molecules.csv")
        )
        self.input_file_edit = QLineEdit(str(resolve_project_path(default_input)))
        browse_input = QPushButton(self._text("browse"))
        browse_input.clicked.connect(self._browse_input_file)
        self.browse_input_button = browse_input
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_file_edit, 1)
        input_row.addWidget(browse_input)

        self.sheet_edit = QLineEdit()
        self.sheet_edit.setPlaceholderText(self._text("sheet_placeholder"))
        self.smiles_column_edit = QLineEdit(
            input_defaults.get("smiles_column", "smiles")
        )
        self.access_code_column_edit = QLineEdit(
            input_defaults.get("access_code_column", "access_code")
        )
        self.input_file_label = QLabel(self._text("file"))
        self.sheet_label = QLabel(self._text("sheet"))
        self.smiles_label = QLabel(self._text("smiles"))
        self.id_label = QLabel(self._text("id"))

        layout.addRow(self.input_file_label, self._wrap_layout(input_row))
        layout.addRow(self.sheet_label, self.sheet_edit)
        layout.addRow(self.smiles_label, self.smiles_column_edit)
        layout.addRow(self.id_label, self.access_code_column_edit)
        return group

    def _build_processing_group(self) -> QGroupBox:
        group = QGroupBox(self._text("processing"))
        self.processing_group = group
        layout = QFormLayout(group)
        self._configure_form_layout(layout)

        self.ph_spin = QDoubleSpinBox()
        self.ph_spin.setRange(0.0, 14.0)
        self.ph_spin.setDecimals(2)
        self.ph_spin.setSingleStep(0.1)
        self.ph_spin.setValue(float(self.base_settings["protonation"].get("ph", 7.4)))
        self.protonation_backend_combo = QComboBox()
        for backend_value, backend_label in (
            ("molgpka", "MolGpKa"),
            ("dimorphite", "Dimorphite-DL (all states)"),
            ("dimorphite_pick", "Dimorphite-DL (single)"),
            ("openbabel", "Open Babel"),
            ("none", "None"),
        ):
            self.protonation_backend_combo.addItem(backend_label, backend_value)
        configured_backend = str(
            self.base_settings["protonation"].get("backend", "molgpka")
        ).lower()
        backend_index = self.protonation_backend_combo.findData(configured_backend)
        if backend_index >= 0:
            self.protonation_backend_combo.setCurrentIndex(backend_index)
        self.tautomer_checkbox = QCheckBox("")
        self.tautomer_checkbox.setChecked(
            bool(self.base_settings.get("tautomer", {}).get("enabled", False))
        )
        self.tautomer_checkbox.toggled.connect(self._toggle_tautomer_state)
        self.tautomer_backend_combo = QComboBox()
        for taut_value, taut_label in (
            ("sphysnet", "sPhysNet-Taut"),
            ("rdkit", "RDKit canonical"),
        ):
            self.tautomer_backend_combo.addItem(taut_label, taut_value)
        configured_tautomer_backend = str(
            self.base_settings.get("tautomer", {}).get("backend", "sphysnet")
        ).lower()
        tautomer_backend_index = self.tautomer_backend_combo.findData(
            configured_tautomer_backend
        )
        if tautomer_backend_index >= 0:
            self.tautomer_backend_combo.setCurrentIndex(tautomer_backend_index)
        self.tautomer_backend_combo.currentIndexChanged.connect(
            self._toggle_tautomer_state
        )
        _sphysnet_cfg = self.base_settings.get("tautomer", {}).get("sphysnet", {})
        self.tautomer_script_edit = QLineEdit(str(_sphysnet_cfg.get("script_path", "")))
        browse_taut_script = QPushButton(self._text("browse"))
        browse_taut_script.clicked.connect(self._browse_tautomer_script)
        self.browse_tautomer_script_button = browse_taut_script
        taut_script_row = QHBoxLayout()
        taut_script_row.addWidget(self.tautomer_script_edit, 1)
        taut_script_row.addWidget(browse_taut_script)
        self.tautomer_script_row = self._wrap_layout(taut_script_row)
        self.tautomer_python_edit = QLineEdit(str(_sphysnet_cfg.get("python", "")))
        browse_taut_python = QPushButton(self._text("browse"))
        browse_taut_python.clicked.connect(self._browse_tautomer_python)
        self.browse_tautomer_python_button = browse_taut_python
        taut_python_row = QHBoxLayout()
        taut_python_row.addWidget(self.tautomer_python_edit, 1)
        taut_python_row.addWidget(browse_taut_python)
        self.tautomer_python_row = self._wrap_layout(taut_python_row)
        self.skip_undefined_stereo_checkbox = QCheckBox("")
        self.skip_undefined_stereo_checkbox.setChecked(
            bool(
                self.base_settings.get("processing", {}).get(
                    "skip_undefined_stereo", False
                )
            )
        )
        self.strict_stereo_checkbox = QCheckBox("")
        self.strict_stereo_checkbox.setChecked(
            bool(
                self.base_settings.get("processing", {}).get(
                    "strict_stereochemistry", False
                )
            )
        )
        self.strict_stereo_checkbox.toggled.connect(self._toggle_stereochemistry_state)
        self.single_undefined_stereo_checkbox = QCheckBox("")
        self.single_undefined_stereo_checkbox.setChecked(
            bool(
                self.base_settings.get("processing", {}).get(
                    "single_undefined_stereocenter_only", False
                )
            )
        )
        self.pm7_checkbox = QCheckBox("")
        self.pm7_checkbox.setChecked(
            bool(self.base_settings.get("pm7", {}).get("enabled", False))
        )
        self.pm7_checkbox.toggled.connect(self._toggle_pm7_state)
        self.mopac_method_combo = QComboBox()
        self.mopac_method_combo.setEditable(True)
        for method_info in COMMON_MOPAC_METHODS:
            self.mopac_method_combo.addItem(method_info.keyword, method_info.keyword)
        configured_method = normalize_mopac_method(
            self.base_settings.get("pm7", {}).get("method", "PM7")
        )
        configured_method_index = self.mopac_method_combo.findData(configured_method)
        if configured_method_index >= 0:
            self.mopac_method_combo.setCurrentIndex(configured_method_index)
        else:
            self.mopac_method_combo.setEditText(configured_method)
        self.mopac_method_combo.currentTextChanged.connect(
            self._update_mopac_method_description
        )
        self.pm7_solvent_checkbox = QCheckBox("")
        self.pm7_solvent_checkbox.setChecked(
            bool(self.base_settings.get("pm7", {}).get("use_eps", True))
        )
        self.pm7_solvent_checkbox.toggled.connect(self._toggle_pm7_state)
        self.pm7_preserve_checkbox = QCheckBox("")
        self.pm7_preserve_checkbox.setChecked(
            bool(self.base_settings.get("pm7", {}).get("preserve_files", False))
        )
        self.pm7_eps_spin = QDoubleSpinBox()
        self.pm7_eps_spin.setRange(1.0, 200.0)
        self.pm7_eps_spin.setDecimals(2)
        self.pm7_eps_spin.setSingleStep(0.1)
        self.pm7_eps_spin.setValue(
            float(self.base_settings.get("pm7", {}).get("eps", 78.39))
        )
        self.mopac_binary_edit = QLineEdit(
            str(self.base_settings.get("pm7", {}).get("binary_path", "")).strip()
        )
        browse_mopac = QPushButton(self._text("browse"))
        browse_mopac.clicked.connect(self._browse_mopac_binary)
        self.browse_mopac_button = browse_mopac
        mopac_row = QHBoxLayout()
        mopac_row.addWidget(self.mopac_binary_edit, 1)
        mopac_row.addWidget(browse_mopac)
        self.ph_label = QLabel(self._text("ph"))
        self.protonation_backend_label = QLabel(self._text("protonation_backend"))
        self.protonation_backend_hint_label = QLabel(
            self._text("protonation_backend_hint")
        )
        self.protonation_backend_hint_label.setObjectName("fieldHintLabel")
        self.protonation_backend_hint_label.setWordWrap(True)
        self.tautomer_label = QLabel(self._text("tautomer"))
        self.tautomer_backend_label = QLabel(self._text("tautomer_backend"))
        self.tautomer_hint_label = QLabel(self._text("tautomer_hint"))
        self.tautomer_hint_label.setObjectName("fieldHintLabel")
        self.tautomer_hint_label.setWordWrap(True)
        self.tautomer_script_label = QLabel(self._text("tautomer_script"))
        self.tautomer_script_hint_label = QLabel(self._text("tautomer_script_hint"))
        self.tautomer_script_hint_label.setObjectName("fieldHintLabel")
        self.tautomer_script_hint_label.setWordWrap(True)
        self.tautomer_python_label = QLabel(self._text("tautomer_python"))
        self.tautomer_python_hint_label = QLabel(self._text("tautomer_python_hint"))
        self.tautomer_python_hint_label.setObjectName("fieldHintLabel")
        self.tautomer_python_hint_label.setWordWrap(True)
        self.pm7_label = QLabel(self._text("pm7"))
        self.skip_undefined_stereo_label = QLabel(self._text("skip_undefined_stereo"))
        self.skip_undefined_stereo_hint_label = QLabel(
            SKIP_UNDEFINED_STEREO_EXPLANATION
        )
        self.skip_undefined_stereo_hint_label.setObjectName("fieldHintLabel")
        self.skip_undefined_stereo_hint_label.setWordWrap(True)
        self.single_undefined_stereo_label = QLabel(
            self._text("strict_stereo_single_only")
        )
        self.single_undefined_stereo_hint_label = QLabel(
            self._text("strict_stereo_single_hint")
        )
        self.single_undefined_stereo_hint_label.setObjectName("fieldHintLabel")
        self.single_undefined_stereo_hint_label.setWordWrap(True)
        self.mopac_method_label = QLabel(self._text("mopac_method"))
        self.mopac_method_hint_label = QLabel(self._text("mopac_method_hint"))
        self.mopac_method_hint_label.setObjectName("fieldHintLabel")
        self.mopac_method_hint_label.setWordWrap(True)
        self.mopac_method_description_label = QLabel("")
        self.mopac_method_description_label.setObjectName("fieldHintLabel")
        self.mopac_method_description_label.setWordWrap(True)
        self.pm7_solvent_label = QLabel(self._text("pm7_solvent"))
        self.pm7_eps_label = QLabel(self._text("pm7_eps"))
        self.pm7_preserve_label = QLabel(self._text("pm7_preserve"))
        self.pm7_preserve_hint_label = QLabel(self._text("pm7_preserve_hint"))
        self.pm7_preserve_hint_label.setObjectName("fieldHintLabel")
        self.pm7_preserve_hint_label.setWordWrap(True)
        self.mopac_binary_label = QLabel(self._text("mopac_binary"))
        self.mopac_binary_hint_label = QLabel(self._text("mopac_binary_hint"))
        self.mopac_binary_hint_label.setObjectName("fieldHintLabel")
        self.mopac_binary_hint_label.setWordWrap(True)
        layout.addRow(self.ph_label, self.ph_spin)
        layout.addRow(self.protonation_backend_label, self.protonation_backend_combo)
        layout.addRow(QLabel(""), self.protonation_backend_hint_label)
        layout.addRow(self.tautomer_label, self._checkbox_cell(self.tautomer_checkbox))
        layout.addRow(self.tautomer_backend_label, self.tautomer_backend_combo)
        layout.addRow(QLabel(""), self.tautomer_hint_label)
        layout.addRow(self.tautomer_script_label, self.tautomer_script_row)
        layout.addRow(QLabel(""), self.tautomer_script_hint_label)
        layout.addRow(self.tautomer_python_label, self.tautomer_python_row)
        layout.addRow(QLabel(""), self.tautomer_python_hint_label)
        layout.addRow(
            self.skip_undefined_stereo_label,
            self._checkbox_cell(self.skip_undefined_stereo_checkbox),
        )
        layout.addRow(QLabel(""), self.skip_undefined_stereo_hint_label)
        self.strict_stereo_label = QLabel(self._text("strict_stereo"))
        layout.addRow(
            self.strict_stereo_label, self._checkbox_cell(self.strict_stereo_checkbox)
        )
        layout.addRow(
            self.single_undefined_stereo_label,
            self._checkbox_cell(self.single_undefined_stereo_checkbox),
        )
        layout.addRow(QLabel(""), self.single_undefined_stereo_hint_label)
        layout.addRow(self.pm7_label, self._checkbox_cell(self.pm7_checkbox))
        layout.addRow(self.mopac_method_label, self.mopac_method_combo)
        layout.addRow(QLabel(""), self.mopac_method_hint_label)
        layout.addRow(QLabel(""), self.mopac_method_description_label)
        layout.addRow(
            self.pm7_solvent_label, self._checkbox_cell(self.pm7_solvent_checkbox)
        )
        layout.addRow(self.pm7_eps_label, self.pm7_eps_spin)
        layout.addRow(
            self.pm7_preserve_label, self._checkbox_cell(self.pm7_preserve_checkbox)
        )
        layout.addRow(QLabel(""), self.pm7_preserve_hint_label)
        layout.addRow(self.mopac_binary_label, self._wrap_layout(mopac_row))
        layout.addRow(QLabel(""), self.mopac_binary_hint_label)
        self._update_mopac_method_description()
        self._toggle_stereochemistry_state()
        self._toggle_pm7_state()
        self._toggle_tautomer_state()
        return group

    def _toggle_tautomer_state(self) -> None:
        enabled = self.tautomer_checkbox.isChecked()
        self.tautomer_backend_combo.setEnabled(enabled)
        self.tautomer_backend_label.setEnabled(enabled)
        # The sPhysNet-Taut path fields are only relevant for that external backend.
        is_sphysnet = str(self.tautomer_backend_combo.currentData()) == "sphysnet"
        show = enabled and is_sphysnet
        for widget in (
            self.tautomer_script_label,
            self.tautomer_script_row,
            self.tautomer_script_hint_label,
            self.tautomer_python_label,
            self.tautomer_python_row,
            self.tautomer_python_hint_label,
        ):
            widget.setVisible(show)

    def _browse_tautomer_script(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._text("tautomer_script"),
            self.tautomer_script_edit.text().strip(),
        )
        if path:
            self.tautomer_script_edit.setText(path)

    def _browse_tautomer_python(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._text("tautomer_python"),
            self.tautomer_python_edit.text().strip(),
        )
        if path:
            self.tautomer_python_edit.setText(path)

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox(self._text("output"))
        self.output_group = group
        layout = QFormLayout(group)
        self._configure_form_layout(layout)

        self.output_dir_edit = QLineEdit(
            default_path_for_display(
                "export", "output_dir", self.base_settings["export"]["output_dir"]
            )
        )
        browse_output = QPushButton(self._text("browse"))
        browse_output.clicked.connect(self._browse_output_dir)
        self.browse_output_button = browse_output
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir_edit, 1)
        output_row.addWidget(browse_output)

        self.export_mode_combo = QComboBox()
        self.export_mode_combo.addItem(
            self._text("mode_separate_mol2"), "separate_mol2"
        )
        self.export_mode_combo.addItem(self._text("mode_separate_sdf"), "separate_sdf")
        self.export_mode_combo.addItem(
            self._text("mode_separate_pdbqt"), "separate_pdbqt"
        )
        self.export_mode_combo.addItem(self._text("mode_single_mol2"), "single_mol2")
        self.export_mode_combo.addItem(self._text("mode_single_sdf"), "single_sdf")
        self.export_mode_combo.addItem(self._text("mode_single_pdbqt"), "single_pdbqt")
        configured_export_mode = self.base_settings["export"].get(
            "mode", "separate_mol2"
        )
        configured_index = max(
            self.export_mode_combo.findData(configured_export_mode), 0
        )
        self.export_mode_combo.setCurrentIndex(configured_index)
        self.export_mode_combo.currentIndexChanged.connect(
            self._toggle_bundle_name_state
        )

        self.bundle_name_edit = QLineEdit(
            self.base_settings["export"].get("bundle_basename", "prepared_ligands")
        )
        self.report_enabled_checkbox = QCheckBox("")
        self.report_enabled_checkbox.setChecked(
            bool(self.base_settings.get("reporting", {}).get("enabled", True))
        )
        self.report_enabled_checkbox.toggled.connect(self._toggle_report_state)
        self.report_dir_edit = QLineEdit(
            default_path_for_display(
                "reporting",
                "report_dir",
                self.base_settings.get("reporting", {}).get(
                    "report_dir", "data/reports"
                ),
            )
        )
        browse_report = QPushButton(self._text("browse"))
        browse_report.clicked.connect(self._browse_report_dir)
        self.browse_report_button = browse_report
        report_row = QHBoxLayout()
        report_row.addWidget(self.report_dir_edit, 1)
        report_row.addWidget(browse_report)
        self.output_dir_label = QLabel(self._text("output_dir"))
        self.export_mode_label = QLabel(self._text("export_mode"))
        self.bundle_name_label = QLabel(self._text("bundle_name"))
        self.bundle_name_hint_label = QLabel(self._bundle_name_hint_text())
        self.bundle_name_hint_label.setObjectName("fieldHintLabel")
        self.bundle_name_hint_label.setWordWrap(True)
        self.report_enabled_label = QLabel(self._text("report_enabled"))
        self.report_dir_label = QLabel(self._text("report_dir"))
        self.report_hint_label = QLabel(self._text("report_hint"))
        self.report_hint_label.setObjectName("fieldHintLabel")
        self.report_hint_label.setWordWrap(True)

        layout.addRow(self.output_dir_label, self._wrap_layout(output_row))
        layout.addRow(self.export_mode_label, self.export_mode_combo)
        layout.addRow(self.bundle_name_label, self.bundle_name_edit)
        layout.addRow(QLabel(""), self.bundle_name_hint_label)
        layout.addRow(
            self.report_enabled_label,
            self._checkbox_cell(self.report_enabled_checkbox),
        )
        layout.addRow(self.report_dir_label, self._wrap_layout(report_row))
        layout.addRow(QLabel(""), self.report_hint_label)
        self._toggle_bundle_name_state()
        self._toggle_report_state()
        return group

    def _toggle_report_state(self) -> None:
        enabled = self.report_enabled_checkbox.isChecked()
        self.report_dir_edit.setEnabled(enabled)
        self.report_dir_label.setEnabled(enabled)
        self.browse_report_button.setEnabled(enabled)

    def _browse_report_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, self._text("report_dir"), self.report_dir_edit.text().strip()
        )
        if directory:
            self.report_dir_edit.setText(directory)

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox(self._text("execution"))
        self.execution_group = group
        layout = QVBoxLayout(group)

        self.run_in_background_checkbox = QCheckBox(self._text("background"))
        self.run_in_background_checkbox.setChecked(True)
        self.run_button = QPushButton(self._text("run"))
        self.run_button.clicked.connect(self._start_workflow)
        self.clear_log_button = QPushButton(self._text("clear_log"))
        self.clear_log_button.clicked.connect(self.log_box.clear)

        layout.addWidget(self.run_in_background_checkbox)
        layout.addWidget(self.run_button)
        layout.addWidget(self.clear_log_button)
        return group

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #ece7de;
                color: #16212f;
                font-size: 11px;
            }
            QWidget#centralSurface {
                background: #ece7de;
            }
            QMenuBar {
                background: #16324f;
                color: #f4f7fb;
                border-bottom: 1px solid #0f2438;
            }
            QLabel#toolbarLabel {
                color: #20354d;
                font-weight: 700;
            }
            QLabel#menuBadge {
                background: #dcb15d;
                color: #13263a;
                border-radius: 12px;
                padding: 7px 14px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.4px;
            }
            QPushButton#menuButton {
                min-width: 132px;
                background: #f4f0e7;
                color: #20354d;
                border: 1px solid #7f91a3;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 700;
                text-align: center;
            }
            QPushButton#menuButton:hover {
                background: #e7dfd1;
                border-color: #5d7388;
            }
            QPushButton#menuButton:pressed {
                background: #d8cfbf;
            }
            QGroupBox {
                border: 1px solid #b5c1cf;
                border-radius: 14px;
                margin-top: 12px;
                padding: 12px;
                background: #fffdfa;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #20354d;
            }
            QLineEdit, QPlainTextEdit, QDoubleSpinBox, QSpinBox {
                border: 1px solid #8798aa;
                border-radius: 10px;
                padding: 7px 9px;
                background: #ffffff;
                color: #172230;
                selection-background-color: #204a72;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QPlainTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
                border: 2px solid #1f5e8a;
            }
            QPlainTextEdit {
                background: #f7f9fc;
                border: 1px solid #7e8ea0;
                color: #172230;
            }
            QCheckBox {
                color: #1a2738;
                spacing: 0px;
                padding: 0px;
                font-weight: 600;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #6f8296;
                border-radius: 5px;
                background: #ffffff;
            }
            QCheckBox::indicator:checked {
                background: #1f5f8b;
                border-color: #184b6d;
            }
            QPushButton {
                border: none;
                border-radius: 11px;
                background: #1f5f8b;
                color: white;
                padding: 9px 14px;
                font-weight: 700;
                text-align: center;
            }
            QPushButton:hover {
                background: #174766;
            }
            QPushButton:pressed {
                background: #13384f;
            }
            QProgressBar {
                border: 1px solid #8998a8;
                border-radius: 9px;
                text-align: center;
                background: #ffffff;
                color: #142030;
                min-height: 22px;
            }
            QProgressBar::chunk {
                background: #d68216;
                border-radius: 7px;
            }
            QLabel#heroTitle {
                font-size: 24px;
                font-weight: 800;
                color: #102235;
            }
            QLabel#heroSubtitle, QLabel#summaryLabel {
                color: #33465a;
                line-height: 1.35;
            }
            QLabel#fieldHintLabel {
                color: #53687e;
                font-size: 11px;
            }
            QLabel {
                background: transparent;
            }
            """
        )
        font = QFont("Segoe UI", 9)
        QApplication.instance().setFont(font)

    def _configure_form_layout(self, layout: QFormLayout) -> None:
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignTop)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self._form_layouts.append(layout)

    def _update_responsive_layout(self, width: int) -> None:
        compact = width < 1100
        if compact:
            self.main_layout.setDirection(QBoxLayout.TopToBottom)
        else:
            self.main_layout.setDirection(QBoxLayout.LeftToRight)

        for layout in self._form_layouts:
            layout.setRowWrapPolicy(
                QFormLayout.WrapAllRows if compact else QFormLayout.WrapLongRows
            )
            layout.setLabelAlignment(
                (Qt.AlignLeft if compact else Qt.AlignRight) | Qt.AlignVCenter
            )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_responsive_layout(event.size().width())

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        wrapper = QWidget()
        wrapper.setLayout(layout)
        return wrapper

    def _checkbox_cell(self, checkbox: QCheckBox) -> QWidget:
        checkbox.setText("")
        checkbox.setFixedWidth(22)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(checkbox, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addStretch(1)
        return self._wrap_layout(layout)

    def _browse_input_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._text("browse_input_title"),
            str(Path(self.input_file_edit.text()).parent),
            self._text("spreadsheet_filter"),
        )
        if path:
            self.input_file_edit.setText(path)

    def _browse_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            self._text("browse_output_title"),
            self.output_dir_edit.text(),
        )
        if path:
            self.output_dir_edit.setText(path)

    def _browse_mopac_binary(self) -> None:
        current = self.mopac_binary_edit.text().strip()
        start_dir = (
            str(Path(current).parent) if current else str(resolve_project_path("."))
        )
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._text("browse_mopac_title"),
            start_dir,
            self._text("executable_filter"),
        )
        if path:
            self.mopac_binary_edit.setText(path)

    def _toggle_bundle_name_state(self) -> None:
        single_file_mode = self.export_mode_combo.currentData() in {
            "single_mol2",
            "single_sdf",
            "single_pdbqt",
        }
        self.bundle_name_edit.setEnabled(True)
        if single_file_mode:
            self.bundle_name_edit.setPlaceholderText(
                self._text("bundle_placeholder_enabled")
            )
        else:
            self.bundle_name_edit.setPlaceholderText(
                self._text("bundle_placeholder_disabled")
            )
        self.bundle_name_hint_label.setText(self._bundle_name_hint_text())

    def _bundle_name_hint_text(self) -> str:
        if self.export_mode_combo.currentData() in {
            "single_mol2",
            "single_sdf",
            "single_pdbqt",
        }:
            return self._text("bundle_hint_single")
        return self._text("bundle_hint_separate")

    def _toggle_pm7_state(self) -> None:
        pm7_enabled = self.pm7_checkbox.isChecked()
        self.mopac_method_combo.setEnabled(pm7_enabled)
        self.pm7_solvent_checkbox.setEnabled(pm7_enabled)
        self.pm7_eps_spin.setEnabled(
            pm7_enabled and self.pm7_solvent_checkbox.isChecked()
        )
        self.pm7_preserve_checkbox.setEnabled(pm7_enabled)
        self.mopac_binary_edit.setEnabled(pm7_enabled)
        self.browse_mopac_button.setEnabled(pm7_enabled)
        self.mopac_method_hint_label.setEnabled(pm7_enabled)
        self.mopac_method_description_label.setEnabled(pm7_enabled)

    def _toggle_stereochemistry_state(self) -> None:
        strict_enabled = self.strict_stereo_checkbox.isChecked()
        self.single_undefined_stereo_checkbox.setEnabled(strict_enabled)
        self.single_undefined_stereo_label.setEnabled(strict_enabled)
        self.single_undefined_stereo_hint_label.setEnabled(strict_enabled)

    def _selected_mopac_method(self) -> str:
        return normalize_mopac_method(self.mopac_method_combo.currentText())

    def _update_mopac_method_description(self) -> None:
        info = get_method_info(self._selected_mopac_method())
        if info is None:
            if self.current_language == "pt":
                self.mopac_method_description_label.setText(
                    "Metodo personalizado. O programa enviara a keyword exatamente como foi digitada para o MOPAC."
                )
            else:
                self.mopac_method_description_label.setText(
                    "Custom method. The program will pass the keyword exactly as typed to MOPAC."
                )
            return

        if self.current_language == "pt":
            self.mopac_method_description_label.setText(
                f"{info.keyword}: {info.title_pt} {info.description_pt}"
            )
        else:
            self.mopac_method_description_label.setText(
                f"{info.keyword}: {info.title_en} {info.description_en}"
            )

    def _build_overrides(self) -> WorkflowOverrides:
        return WorkflowOverrides(
            input_file=self.input_file_edit.text().strip(),
            sheet_name=self.sheet_edit.text().strip(),
            smiles_column=self.smiles_column_edit.text().strip(),
            access_code_column=self.access_code_column_edit.text().strip(),
            output_dir=self.output_dir_edit.text().strip(),
            export_mode=str(self.export_mode_combo.currentData()),
            bundle_basename=self.bundle_name_edit.text().strip(),
            ph=float(self.ph_spin.value()),
            protonation_backend=str(self.protonation_backend_combo.currentData()),
            skip_undefined_stereo=self.skip_undefined_stereo_checkbox.isChecked(),
            strict_stereochemistry=self.strict_stereo_checkbox.isChecked(),
            single_undefined_stereocenter_only=self.single_undefined_stereo_checkbox.isChecked(),
            pm7_enabled=self.pm7_checkbox.isChecked(),
            mopac_method=self._selected_mopac_method(),
            pm7_use_eps=self.pm7_solvent_checkbox.isChecked(),
            pm7_eps=float(self.pm7_eps_spin.value()),
            pm7_preserve_files=self.pm7_preserve_checkbox.isChecked(),
            mopac_binary=self.mopac_binary_edit.text().strip(),
            run_in_background=self.run_in_background_checkbox.isChecked(),
            tautomer_enabled=self.tautomer_checkbox.isChecked(),
            tautomer_backend=str(self.tautomer_backend_combo.currentData()),
            tautomer_script=self.tautomer_script_edit.text().strip(),
            tautomer_python=self.tautomer_python_edit.text().strip(),
            report_enabled=self.report_enabled_checkbox.isChecked(),
            report_dir=self.report_dir_edit.text().strip(),
        )

    def _start_workflow(self) -> None:
        overrides = self._build_overrides()
        if not overrides.input_file:
            QMessageBox.warning(self, APP_NAME, self._text("warning_input"))
            return

        runtime_overrides = {
            "input": {
                "file_path": overrides.input_file,
                "sheet_name": overrides.sheet_name or None,
                "smiles_column": overrides.smiles_column or "smiles",
                "access_code_column": overrides.access_code_column or "access_code",
            },
            "export": {
                "output_dir": overrides.output_dir
                or str(resolve_project_path("data/processed")),
                "mode": overrides.export_mode,
                "bundle_basename": overrides.bundle_basename,
            },
            "processing": {
                "skip_undefined_stereo": overrides.skip_undefined_stereo,
                "strict_stereochemistry": overrides.strict_stereochemistry,
                "single_undefined_stereocenter_only": overrides.single_undefined_stereocenter_only,
            },
            "protonation": {
                "ph": overrides.ph,
                "backend": overrides.protonation_backend,
                "enabled": overrides.protonation_backend != "none",
            },
            "tautomer": {
                "enabled": overrides.tautomer_enabled,
                "backend": overrides.tautomer_backend,
                "sphysnet": {
                    "script_path": overrides.tautomer_script,
                    "python": overrides.tautomer_python,
                    "num_confs": int(
                        self.base_settings.get("tautomer", {})
                        .get("sphysnet", {})
                        .get("num_confs", 100)
                    ),
                },
            },
            "reporting": {
                "enabled": overrides.report_enabled,
                "report_dir": overrides.report_dir
                or self.base_settings.get("reporting", {}).get(
                    "report_dir", "data/reports"
                ),
            },
            "pm7": {
                "enabled": overrides.pm7_enabled,
                "method": overrides.mopac_method,
                "use_eps": overrides.pm7_use_eps,
                "eps": overrides.pm7_eps,
                "preserve_files": overrides.pm7_preserve_files,
                "binary_path": overrides.mopac_binary,
            },
            "ui": {"language": self.current_language},
        }
        settings = resolve_settings_paths(
            merge_settings(self.base_settings, runtime_overrides)
        )

        self.run_button.setEnabled(False)
        self.log_box.clear()
        self.progress_label.setText(self._text("status_initializing"))
        self.progress_bar.setValue(0)
        self._last_payload = None

        self._thread = QThread(self)
        self._worker = WorkflowWorker(settings)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_message.connect(self.log_box.appendPlainText)
        self._worker.progress_changed.connect(self._update_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()
        if overrides.run_in_background:
            self.showMinimized()

    def _update_progress(self, current: int, total: int, message: str) -> None:
        self.progress_label.setText(message)
        percentage = 0 if total == 0 else int((current / total) * 100)
        self.progress_bar.setValue(min(percentage, 100))

    def _set_summary(self, payload: dict) -> None:
        summary_lines = [
            f"{self._text('summary_status')}: {payload['status']}",
            f"{self._text('summary_ph')}: {payload['ph']:.2f}",
            f"{self._text('summary_pm7')}: {self._describe_pm7(payload)}",
            f"{self._text('summary_eps')}: {self._describe_eps(payload)}",
            f"{self._text('summary_pm7_files')}: {self._describe_pm7_files(payload)}",
            f"{self._text('summary_export')}: {self._describe_export_mode(payload['export_mode'])}",
            f"{self._text('summary_records')}: {payload['structure_records_exported']}",
            f"{self._text('summary_files')}: {payload['structure_files_written']}",
            (
                f"{self._text('summary_stereo')}: {payload['stereochemistry_issues']} "
                f"({self._text('summary_enumerated')}: {payload['stereochemistry_enumerated']}, "
                f"{self._text('summary_skipped')}: {payload['stereochemistry_skipped']})"
            ),
            f"{self._text('summary_failures')}: {payload['failures']}",
            f"{self._text('summary_report')}: {payload['report_path']}",
        ]
        if payload["log_file_path"]:
            summary_lines.append(
                f"{self._text('summary_log')}: {payload['log_file_path']}"
            )
        self.summary_label.setText("\n".join(summary_lines))

    def _on_finished(self, payload: dict) -> None:
        self._last_payload = payload
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText(self._text("status_completed"))
        self._set_summary(payload)

    def _on_failed(self, message: str) -> None:
        self._last_payload = None
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(self._text("status_failed"))
        self.summary_label.setText(
            self._text("failure_summary").format(message=message)
        )
        self.log_box.appendPlainText(message)

    def _cleanup_thread(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            self._text("about_title"),
            "\n".join(
                [
                    f"{APP_NAME} {APP_VERSION}",
                    f"{self._text('author_label')}: {AUTHOR_SUMMARY}",
                    AUTHOR_EMAIL,
                    "",
                    f"{self._text('license_label')}: {PROJECT_LICENSE}",
                    self._text("about_notice"),
                ]
            ),
        )

    def _describe_export_mode(self, export_mode: str) -> str:
        descriptions = {
            "separate_mol2": self._text("mode_separate_mol2"),
            "separate_sdf": self._text("mode_separate_sdf"),
            "separate_pdbqt": self._text("mode_separate_pdbqt"),
            "single_mol2": self._text("mode_single_mol2"),
            "single_sdf": self._text("mode_single_sdf"),
            "single_pdbqt": self._text("mode_single_pdbqt"),
        }
        return descriptions.get(export_mode, export_mode)

    def _describe_pm7(self, payload: dict) -> str:
        if not payload.get("pm7_enabled"):
            return self._text("pm7_disabled")
        method = payload.get("pm7_method") or "PM7"
        return self._text("pm7_enabled_summary").format(
            method=method, count=payload.get("pm7_optimized", 0)
        )

    def _describe_eps(self, payload: dict) -> str:
        value = payload.get("pm7_solvent_eps")
        if value is None:
            return self._text("gas_phase")
        return f"{value:.2f}"

    def _describe_pm7_files(self, payload: dict) -> str:
        if not payload.get("pm7_files_preserved"):
            return self._text("pm7_disabled")
        count = int(payload.get("pm7_preserved_file_count", 0))
        directory = str(payload.get("pm7_preserved_files_dir", "")).strip()
        if directory:
            return f"{count} -> {directory}"
        return str(count)
